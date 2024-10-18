# coding: utf-8

# https://forum.omz-software.com/topic/2792/webview-bug
html = """

<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Scroll Animation</title>
    <style>
        body, html {
            margin: 0;
            padding: 0;
            overflow-x: hidden;
            overflow-y: scroll;
            height: 100%;
        }
        section {
            height: 100vh;
            width: 100%;
            position: relative;
        }
        canvas {
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
        }
    </style>
</head>
<body>
    <section>
        <canvas id="animationCanvas"></canvas>
    </section>
    <script>
        const canvas = document.getElementById('animationCanvas');
        const context = canvas.getContext('2d');

        const frameCount = 148;
        const currentFrame = index => (
          `static/images/${index.toString().padStart(4, '0')}.jpg`
        );

        const img = new Image();
        img.src = currentFrame(1);
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
        img.onload = function() {
          context.drawImage(img, 0, 0);
        };

        const updateImage = index => {
          img.src = currentFrame(index);
          context.drawImage(img, 0, 0);
        };

        window.addEventListener('scroll', () => {  
          const scrollTop = document.documentElement.scrollTop;
          const maxScrollTop = document.documentElement.scrollHeight - window.innerHeight;
          const scrollFraction = scrollTop / maxScrollTop;
          const frameIndex = Math.min(
            frameCount - 1,
            Math.floor(scrollFraction * frameCount)
          );

          requestAnimationFrame(() => updateImage(frameIndex + 1));
        });
    </script>
    test
</body>
</html>
"""
import ui
from objc_util import ObjCInstance, on_main_thread

web_view = ui.WebView(frame=(0,0,500,500))
web_view.present('sheet')
web_view.load_html(html)

js = 'alert(document.title)'
wv = ObjCInstance(web_view).subviews()[0]
on_main_thread(wv.stringByEvaluatingJavaScriptFromString_)(js)
