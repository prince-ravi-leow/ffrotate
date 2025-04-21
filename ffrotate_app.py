import webview

from ffrotate import ffrotate_app  

ffrotate_app.launch(prevent_thread_lock=True)
webview.settings['ALLOW_DOWNLOADS'] = True

webview.create_window("ffrotate", ffrotate_app.local_url)  
webview.start()