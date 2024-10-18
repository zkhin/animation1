# coding: utf-8

# Captured from: _https://forum.omz-software.com/topic/2485/how-to-create-more-than-one-ui-and-interact-between-them_

import sound, time, ui

def screen(title='title'):
	button = ui.Button(title=title)
	button.action = lambda sender: sender.close()
	button.present(hide_title_bar=True)
	button.wait_modal()
	
for title in 'login configure play'.split():
	screen(title)
	
for i in xrange(7):
	sound.play_effect('arcade:Explosion_{}'.format(i+1))
	time.sleep(1)
	
###==============================

# [ ... ]
ui.load_view('login').present('sheet')
# [ ... ]
ui.load_view('configure').present('sheet')
# [ ... ]
ui.load_view('play').present('fullscreen')
# [ ... ]

