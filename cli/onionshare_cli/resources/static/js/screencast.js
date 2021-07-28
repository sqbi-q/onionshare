var onion_host = document.getElementById('onion-host').value;

var video = document.getElementById('video');
if (Hls.isSupported()) {
    var hls = new Hls();
    hls.loadSource('http://' + onion_host + '/live/stream.m3u8');
    hls.attachMedia(video);
}