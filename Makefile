MMARK:=mmark

docs = draft-open-contributions-descriptor.md 

all: $(docs)
		$(MMARK) $< > $<.xml
		xml2rfc --text $<.xml
		xml2rfc --html $<.xml

