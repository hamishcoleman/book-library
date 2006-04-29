
localdir := ~hamish/WWW/library
testdir  := $(localdir)/test

files    := library.cgi

all:
	@echo I think you want make test or make local

#
# Generic rules
#
# TODO - see if I cannot consolodate the extra words for test vs local

$(localdir)/%.cgi $(testdir)/%.cgi: %.cgi
	install -m a+rx $^ $@

$(localdir)/% $(testdir)/%: %
	install -m a+r $^ $@

# the two install targets
test:	$(testdir) \
	$(addprefix $(testdir)/,$(files)) \
	$(localdir)/db/library.sql

local:	$(localdir) \
	$(addprefix $(localdir)/,$(files)) \
	$(localdir)/db/library.sql

$(localdir) $(testdir):
	install -d -m a+rx,u+rwx $@

$(testdir): $(localdir)

# Argh, I always have issues with makeing directories.  This one always thinks
# it needs updating ...  oh well..
#
#$(localdir)/db: $(localdir)
#	install -d -m a+rwx $@

$(localdir)/db/library.sql: library.sql
	@echo WARNING: database schema has changed
	@echo          manual intervention required

# FIXME - install a database if this is not already one there

library.sql: schema.txt
	rm -f $@
	sqlite3 $@ <$^

