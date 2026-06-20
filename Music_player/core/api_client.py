"""API"""
import requests
from typing import Optional, Dict, Any, List
from core.config import Config


class APIError(Exception):
    pass


class APIClient:
    def __init__(self, base_url: str = Config.DEFAULT_API_URL):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://music.163.com/"
        })
    
    def set_base_url(self, url: str):
        self.base_url = url.rstrip("/")
    
    def check_alive(self) -> bool:
        try:
            r = self.session.get(f"{self.base_url}/login/status", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
    def search_playlists(self, keywords: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索歌单"""
        url = f"{self.base_url}/search"
        params = {"keywords": keywords, "limit": limit, "type": 1000}
        try:
            r = self.session.get(url, params=params, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("result"):
                playlists = data["result"].get("playlists", [])
                return [{
                    "id": p["id"],
                    "name": p["name"],
                    "creator": p.get("creator", {}).get("nickname", ""),
                    "track_count": p.get("trackCount", 0),
                    "play_count": p.get("playCount", 0)
                } for p in playlists]
            return []
        except Exception as e:
            raise APIError(f"搜索失败: {e}")
    
    def search_songs(self, keywords: str, limit: int = 30) -> List[Dict[str, Any]]:
        """搜索歌曲"""
        url = f"{self.base_url}/search"
        params = {"keywords": keywords, "limit": limit, "type": 1}
        try:
            r = self.session.get(url, params=params, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("result"):
                songs = data["result"].get("songs", [])
                return [{
                    "id": s["id"],
                    "name": s["name"],
                    "artists": [a["name"] for a in s.get("ar", [])],
                    "album": s.get("al", {}).get("name", ""),
                    "duration": s.get("dt", 0)  # 毫秒
                } for s in songs]
            return []
        except Exception as e:
            raise APIError(f"搜索失败: {e}")
    
    def search_mvs(self, keywords: str, limit: int = 20) -> List[Dict[str, Any]]:
        """搜索MV"""
        url = f"{self.base_url}/search"
        params = {"keywords": keywords, "limit": limit, "type": 1004}
        try:
            r = self.session.get(url, params=params, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("result"):
                mvs = data["result"].get("mvs", [])
                return [{
                    "id": m["id"],
                    "name": m["name"],
                    "artist": m.get("artistName", ""),
                    "duration": m.get("duration", 0)
                } for m in mvs]
            return []
        except Exception as e:
            raise APIError(f"搜索失败: {e}")
    
    def get_song_detail(self, song_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/song/detail?ids={song_id}"
        try:
            r = self.session.get(url, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("songs"):
                return {
                    "id": song_id,
                    "name": data["songs"][0]["name"],
                    "artists": [a["name"] for a in data["songs"][0].get("ar", [])],
                    "album": data["songs"][0].get("al", {}).get("name", "")
                }
            raise APIError(f"获取失败: {data}")
        except Exception as e:
            raise APIError(f"请求异常: {e}")
    
    def get_playlist_detail(self, playlist_id: str) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/playlist/detail?id={playlist_id}"
        try:
            r = self.session.get(url, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("playlist"):
                tracks = data["playlist"].get("tracks", [])
                return [{
                    "id": t["id"],
                    "name": t["name"],
                    "artists": [a["name"] for a in t.get("ar", [])],
                    "album": t.get("al", {}).get("name", "")
                } for t in tracks]
            raise APIError(f"获取失败: {data}")
        except Exception as e:
            raise APIError(f"请求异常: {e}")
    
    def get_download_url(self, song_id: str, br = 320000) -> Optional[str]:
        # br can be int bitrate (e.g. 320000) or the string 'flac' for lossless
        br_param = 999000 if br == "flac" else br
        url = f"{self.base_url}/song/url?id={song_id}&br={br_param}"
        try:
            r = self.session.get(url, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("data"):
                return data["data"][0].get("url")
            return None
        except Exception:
            return None
    
    def download_song(self, url: str) -> Optional[bytes]:
        try:
            r = self.session.get(url, stream=True, timeout=Config.TIMEOUT_DOWNLOAD)
            if r.status_code == 200:
                return r.content
            return None
        except Exception:
            return None
    
    def get_mv_download_url(self, mv_id: str) -> Optional[str]:
        """获取MV下载链接"""
        url = f"{self.base_url}/mv/url?id={mv_id}"
        try:
            r = self.session.get(url, timeout=Config.TIMEOUT_API)
            data = r.json()
            if data.get("code") == 200 and data.get("data"):
                return data["data"].get("url")
            return None
        except Exception:
            return None
