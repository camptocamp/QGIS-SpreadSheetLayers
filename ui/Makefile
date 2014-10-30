
UI_FILES = $(wildcard *.ui)


###################### DON'T EDIT FURTHER ###################################

COMPILED_UI = $(UI_FILES:%.ui=%.py)

default : ui

clean:
	rm -f $(COMPILED_UI)
	rm -f *.pyc

ui: $(COMPILED_UI)

# Conversion rules

%.py : %.ui
	pyuic4 -o $@ $<
