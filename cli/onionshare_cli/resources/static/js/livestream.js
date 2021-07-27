var video = document.getElementById('video');
if (Hls.isSupported()) {
    var hls = new Hls();
    hls.loadSource('/live/stream.m3u8');
    hls.attachMedia(video);
}