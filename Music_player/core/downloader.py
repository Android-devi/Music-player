"""下载器"""
import os
import time
from pathlib import Path
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt6.QtCore import QThread, pyqtSignal, QMutex
from core.api_client import APIClient, APIError
from core.config import Config
from utils.helpers import clean_filename, format_number
from utils.history import DownloadHistory
from language import i18n


class DownloadTask(QThread):
    log_message = pyqtSignal(str)
    progress_update = pyqtSignal(int, int)
    song_start = pyqtSignal(str, int, int)
    song_complete = pyqtSignal(str, bool)
    download_finished = pyqtSignal(bool)
    api_status = pyqtSignal(bool, str)
    
    def __init__(self, api_url: str, download_path: str, bitrate = 320000):
        super().__init__()
        self.api = APIClient(api_url)
        self.download_path = Path(download_path)
        self.history = DownloadHistory()
        # normalize bitrate: use string "flac" for lossless, ints for kbps values
        if isinstance(bitrate, str) and bitrate.lower() == "flac":
            self.bitrate = "flac"
        else:
            try:
                self.bitrate = int(bitrate)
            except Exception:
                self.bitrate = 320000
        self._running = True
        self._completed = 0
        self._total = 0
        self._success = 0
        self._progress_mutex = QMutex()
        self.task_type = 2  # default playlist
        self.task_id = ""
    
    def set_task(self, task_type: int, task_id: str):
        self.task_type = task_type
        self.task_id = task_id
    
    def set_bitrate(self, bitrate):
        # normalize same as constructor
        if isinstance(bitrate, str) and bitrate.lower() == "flac":
            self.bitrate = "flac"
        else:
            try:
                self.bitrate = int(bitrate)
            except Exception:
                self.bitrate = 320000
    
    def stop(self):
        self._running = False
        self.wait(1000)
    
    def _ensure_dir(self):
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def _check_exists(self, name: str, ext: str = None) -> bool:
        if ext is None:
            ext = "flac" if self.bitrate == "flac" else "mp3"
        return (self.download_path / f"{name}.{ext}").exists()
    
    def _save_file(self, name: str, data: bytes, ext: str = None) -> bool:
        try:
            if ext is None:
                ext = "flac" if self.bitrate == "flac" else "mp3"
            path = self.download_path / f"{name}.{ext}"
            with open(path, "wb") as f:
                f.write(data)
            
            file_size = path.stat().st_size
            
            # 音频文件小于1MB认为是试听版
            if ext in ("mp3", "flac") and file_size < 1000 * 1024:
                self.log_message.emit(f"{name} - {i18n.tr('trial_deleted')}")
                path.unlink()
                return False
            
            return True
        except Exception as e:
            self.log_message.emit(f"{i18n.tr('save_fail')}: {e}")
            return False
    
    def _download_single(self, song_id: str, song_name: Optional[str] = None,
                        index: int = 0, total: int = 1) -> bool:
        try:
            if not self._running:
                return False
            
            if not song_name:
                detail = self.api.get_song_detail(song_id)
                song_name = detail["name"]
            
            song_name = clean_filename(song_name)
            self.song_start.emit(song_name, index, total)
            
            # 检查历史记录 - 断点续传
            if self.history.is_completed(song_id, "song", self.task_id):
                self.log_message.emit(f"⊘ {song_name} - {i18n.tr('history_skip')}")
                return True
            
            if self._check_exists(song_name):
                self.log_message.emit(f"⊘ {song_name} - {i18n.tr('exists_skip')}")
                self.history.record(song_id, song_name, "song", "skipped", self.task_id)
                return True
            
            url = self.api.get_download_url(song_id, self.bitrate)
            if not url:
                self.log_message.emit(f"{song_name} - {i18n.tr('no_copyright')}")
                self.history.record(song_id, song_name, "song", "failed", self.task_id)
                return False
            
            data = self.api.download_song(url)
            if not data or len(data) < 1024:
                self.log_message.emit(f"{song_name} - {i18n.tr('data_error')}")
                self.history.record(song_id, song_name, "song", "failed", self.task_id)
                return False
            
            if self._save_file(song_name, data):
                self.log_message.emit(f"{song_name} - {i18n.tr('done')}")
                self.history.record(song_id, song_name, "song", "completed", self.task_id)
                return True
            else:
                self.history.record(song_id, song_name, "song", "failed", self.task_id)
                return False
            
        except APIError as e:
            self.log_message.emit(f"{song_name or song_id} - {e}")
            self.history.record(song_id, song_name or song_id, "song", "failed", self.task_id)
            return False
        except Exception as e:
            self.log_message.emit(f"{i18n.tr('error')}: {e}")
            self.history.record(song_id, song_name or song_id, "song", "failed", self.task_id)
            return False
    
    def _download_mv_single(self, mv_id: str, mv_name: Optional[str] = None,
                             index: int = 0, total: int = 1) -> bool:
        try:
            if not self._running:
                return False
            
            if not mv_name:
                mv_name = mv_id
            
            mv_name = clean_filename(mv_name)
            self.song_start.emit(mv_name, index, total)
            
            # 检查历史记录
            if self.history.is_completed(mv_id, "mv", self.task_id):
                self.log_message.emit(f"⊘ {mv_name} - {i18n.tr('history_skip')}")
                return True
            
            if self._check_exists(mv_name, "mp4"):
                self.log_message.emit(f"⊘ {mv_name} - {i18n.tr('exists_skip')}")
                self.history.record(mv_id, mv_name, "mv", "skipped", self.task_id)
                return True
            
            url = self.api.get_mv_download_url(mv_id)
            if not url:
                self.log_message.emit(f"{mv_name} - {i18n.tr('no_copyright')}")
                self.history.record(mv_id, mv_name, "mv", "failed", self.task_id)
                return False
            
            data = self.api.download_song(url)
            if not data or len(data) < 1024:
                self.log_message.emit(f"{mv_name} - {i18n.tr('data_error')}")
                self.history.record(mv_id, mv_name, "mv", "failed", self.task_id)
                return False
            
            if self._save_file(mv_name, data, "mp4"):
                self.log_message.emit(f"{mv_name} - {i18n.tr('done')}")
                self.history.record(mv_id, mv_name, "mv", "completed", self.task_id)
                return True
            else:
                self.history.record(mv_id, mv_name, "mv", "failed", self.task_id)
                return False
            
        except APIError as e:
            self.log_message.emit(f"{mv_name or mv_id} - {e}")
            self.history.record(mv_id, mv_name or mv_id, "mv", "failed", self.task_id)
            return False
        except Exception as e:
            self.log_message.emit(f"{i18n.tr('error')}: {e}")
            self.history.record(mv_id, mv_name or mv_id, "mv", "failed", self.task_id)
            return False
    
    def _update_progress_safe(self, current, total):
        self._progress_mutex.lock()
        try:
            self.progress_update.emit(current, total)
        finally:
            self._progress_mutex.unlock()
    
    def run(self):
        try:
            self.api_status.emit(False, i18n.tr("api_checking"))
            if not self.api.check_alive():
                self.api_status.emit(False, i18n.tr("api_offline"))
                self.log_message.emit(i18n.tr("api_not_started"))
                self.download_finished.emit(False)
                return
            
            self.api_status.emit(True, i18n.tr("api_online"))
            self._ensure_dir()
            
            if self.task_type == 1:  # 单曲
                self._update_progress_safe(0, 1)
                success = self._download_single(self.task_id, index=1, total=1)
                self._update_progress_safe(1, 1)
                self.download_finished.emit(success)
                return
            
            if self.task_type == 3:  # MV
                self._update_progress_safe(0, 1)
                success = self._download_mv_single(self.task_id, index=1, total=1)
                self._update_progress_safe(1, 1)
                self.download_finished.emit(success)
                return
            
            # task_type == 2: 歌单
            self.log_message.emit(i18n.tr("fetch_playlist"))
            try:
                songs = self.api.get_playlist_detail(self.task_id)
            except APIError as e:
                self.log_message.emit(f"{i18n.tr('playlist_fetch_fail')}: {e}")
                self.download_finished.emit(False)
                return
            
            total_songs = len(songs)
            if not total_songs:
                self.log_message.emit(i18n.tr("playlist_empty_msg"))
                self.download_finished.emit(False)
                return
            
            # 断点续传：过滤掉历史记录中已完成的
            pending_songs = []
            skipped_count = 0
            for song in songs:
                if not self.history.is_completed(str(song["id"]), "song", self.task_id):
                    pending_songs.append(song)
                else:
                    skipped_count += 1
            
            if skipped_count > 0:
                self.log_message.emit(f"{i18n.tr('resume_skip')} {skipped_count} {i18n.tr('already_downloaded')}")
            
            self._total = len(pending_songs)
            if not self._total:
                self.log_message.emit(i18n.tr("playlist_all_done"))
                self._update_progress_safe(total_songs, total_songs)
                self.download_finished.emit(True)
                return
            
            self.log_message.emit(f"{i18n.tr('playlist_total')} {format_number(total_songs)} {i18n.tr('songs_count')}，{i18n.tr('pending')} {format_number(self._total)} {i18n.tr('songs_count')}")
            self._update_progress_safe(0, self._total)
            
            self._completed = 0
            self._success = 0
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_song = {}
                for i, song in enumerate(pending_songs, 1):
                    if not self._running:
                        break
                    
                    future = executor.submit(
                        self._download_single,
                        str(song["id"]),
                        song["name"],
                        i,
                        self._total
                    )
                    future_to_song[future] = song
                    time.sleep(0.1)
                
                for future in as_completed(future_to_song):
                    if not self._running:
                        executor.shutdown(wait=False)
                        break
                    
                    if future.result():
                        self._success += 1
                    
                    self._completed += 1
                    self._update_progress_safe(self._completed, self._total)
            
            total_success = self._success + skipped_count
            self._update_progress_safe(self._total, self._total)
            self.log_message.emit(f"{i18n.tr('complete_result')} {total_success}/{total_songs} ({i18n.tr('this_time')} {self._success}/{self._total})")
            self.download_finished.emit(True)
            
        except Exception as e:
            self.log_message.emit(f"{i18n.tr('severe_error')}: {e}")
            self.download_finished.emit(False)
