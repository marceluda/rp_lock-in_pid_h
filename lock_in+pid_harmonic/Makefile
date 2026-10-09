#
#

APP=$(notdir $(CURDIR:%/=%))

-include ../_settings.env
-include ../_build_number


# Versioning system
BUILD_NUMBER ?= 0
REVISION ?= devbuild
VER:=$(shell cat info/info.json | grep version | sed -e 's/.*:\ *\"//' | sed -e 's/-.*//')

INSTALL_DIR ?= .


CONTROLLERHF   = controllerhf.so
CONTROLLER_DBG = controllerhf_dbg.so
CONTROLLER_RLD = controllerhf_rld.so

# FPGA: Vivado 2020.1, RedPitaya-FPGA structure (fpga/, project v0.94, model Z10).
# fpga/Makefile loads Vivado 2020.1 by itself in a clean environment, so it does
# not mix with the Vivado 2015.2 + Linaro environment of ../settings.sh used for C.
# It produces red_pitaya.bit and, with bootgen, fpga.bit.bin (Ecosystem 2.0:
# loaded with fpgautil by fpga.sh).
FPGA_BIN  = fpga.bit.bin
FPGA_PRJ ?= v0.94
FPGA_OUT  = fpga/prj/$(FPGA_PRJ)/out


CFLAGS += -DVERSION=$(VER)-$(BUILD_NUMBER) -DREVISION=$(REVISION)
export CFLAGS


# fpga/app are PHONY: with fpga.sh present, make's implicit rule '%: %.sh' would
# otherwise turn the target 'fpga' (a directory) into 'cat fpga.sh > fpga'
.PHONY: clean clean_fpga clean_app clean_target fpga app c_tools

all: $(CONTROLLERHF) c_tools fpga

$(CONTROLLERHF):
	$(MAKE) -C src clean
	# Turn on DEBUG
	sed 's?/* *#define DEBUG 1.*?#define DEBUG 1? ' -i src/main.h
	$(MAKE) -C src
	mv $(CONTROLLERHF) $(CONTROLLER_DBG)
	$(MAKE) -C src clean
	# Turn off DEBUG
	sed ' s?/* *#define DEBUG 1.*?// #define DEBUG 1? ' -i src/main.h
	# Turn on RELOAD
	sed "s?/\\*RELOAD_DOCK_START\\*/.*/\\*RELOAD_DOCK_END\\*/?/*RELOAD_DOCK_START*/ PARAMS_LOCK_PARAMS - 1 /*RELOAD_DOCK_END*/?"  -i src/main.c
	cp src/main.c src/main_$(CONTROLLER_RLD)_.c
	$(MAKE) -C src
	mv $(CONTROLLERHF) $(CONTROLLER_RLD)
	$(MAKE) -C src clean
	# Turn off RELOAD
	sed "s?/\\*RELOAD_DOCK_START\\*/.*/\\*RELOAD_DOCK_END\\*/?/*RELOAD_DOCK_START*/ PARAMS_NUM /*RELOAD_DOCK_END*/?"  -i src/main.c
	$(MAKE) -C src
	cp src/main.c src/main_$(CONTROLLERHF)_.c


app: $(CONTROLLERHF) c_tools

# Helper tools in c/ (lock, osc, streaming, stream_tcp_osc_cmd): cross compiled with the
# flags of c/Makefile, so the binaries packaged in target/ always match their sources
c_tools:
	$(MAKE) -C c all

fpga: red_pitaya.bit fpga.bit $(FPGA_BIN)

red_pitaya.bit:
	$(MAKE) -C fpga all PRJ=$(FPGA_PRJ)
	cp $(FPGA_OUT)/red_pitaya.bit .

fpga.bit: red_pitaya.bit
	cp red_pitaya.bit ./fpga.bit

# .bit -> .bin for Ecosystem 2.0: made by fpga/Makefile (bootgen of Vivado 2020.1)
$(FPGA_BIN): red_pitaya.bit
	$(MAKE) -C fpga bin PRJ=$(FPGA_PRJ)
	cp $(FPGA_OUT)/fpga.bit.bin $(FPGA_BIN)



target/$(APP): red_pitaya.bit $(FPGA_BIN) $(CONTROLLERHF) c_tools index.html
	mkdir -p target/$(APP)
	cp -r $(CONTROLLERHF) c nginx.conf fpga.conf fpga.sh $(FPGA_BIN) info css js py red_pitaya.bit index.html target/$(APP)
	rm target/$(APP)/info/icon_*.png
	chmod 755 target/$(APP)/fpga.sh  # 2.0 runs it with system(): needs the exec bit (it is 644 in git)
	cp -r upload_app.sh target/
	cp -r ../resources target/
	cp ../CHANGELOG.md ../README.md target/
	mkdir -p target/$(APP)/py
	# No Python caches in target/ nor in the packages (py/__pycache__, resources/**/__pycache__, *.pyc)
	find target -name __pycache__ -type d -prune -exec rm -rf {} +
	find target \( -name '*.pyc' -o -name '*.pyo' \) -type f -delete
	sed -i target/$(APP)/info/info.json -e 's/REVISION/$(REVISION)/'
	sed -i target/$(APP)/info/info.json -e 's/BUILD_NUMBER/$(BUILD_NUMBER)/'
	sed -i target/$(APP)/index.html -e "s/\(\\s*\)var\\s*app_version\\s*=\\s*'VERSION'\\s*;\\s*/\\1var app_version = '$(VER)-$(BUILD_NUMBER)-$(REVISION)';/"


zip: $(CONTROLLERHF) target/$(APP)
	mkdir -p ../archive
	cd target; zip -r $(INSTALL_DIR)/$(APP)-$(VER)-$(BUILD_NUMBER)-$(REVISION).zip *
	mv target/$(APP)-$(VER)-$(BUILD_NUMBER)-$(REVISION).zip ../archive/.

tar: $(CONTROLLERHF) target/$(APP)
	mkdir -p ../archive
	cd target; tar -czf $(INSTALL_DIR)/$(APP)-$(VER)-$(BUILD_NUMBER)-$(REVISION).tar.gz *
	mv target/$(APP)-$(VER)-$(BUILD_NUMBER)-$(REVISION).tar.gz ../archive/.

clean_target:
	-$(RM) target -rf

clean_app:
	$(MAKE) -C src clean
	$(MAKE) -C c clean
	-$(RM) target -rf
	-$(RM) *.so
	echo "BUILD_NUMBER=$$(( $(BUILD_NUMBER) + 1 ))" > ../_build_number

clean_fpga:
	$(MAKE) -C fpga clean PRJ=$(FPGA_PRJ)
	-$(RM) target -rf
	-$(RM) red_pitaya.bit fpga.bit $(FPGA_BIN) fpga.bif
	echo "BUILD_NUMBER=$$(( $(BUILD_NUMBER) + 1 ))" > ../_build_number

clean: clean_app clean_fpga clean_target



upload_bit:
	ssh $(RPIP) $(RPOPTS) "PATH_REDPITAYA=/opt/redpitaya /boot/sbin/rw ; rm /opt/redpitaya/www/apps/$(APP)/red_pitaya.bit"
	scp $(RPSCP) red_pitaya.bit  root@$(RPIP):/opt/redpitaya/www/apps/$(APP)/

upload: target/$(APP)
	ssh $(RPIP) $(RPOPTS) "PATH_REDPITAYA=/opt/redpitaya /boot/sbin/rw ; rm -rf /opt/redpitaya/www/apps/$(APP) ; mkdir -p /opt/redpitaya/www/apps/$(APP)"
	cd target/$(APP) ; scp  $(RPSCP) -r controllerhf.so css js py c nginx.conf fpga.conf fpga.sh $(FPGA_BIN) index.html info red_pitaya.bit  root@$(RPIP):/opt/redpitaya/www/apps/$(APP)/

upload_html: target/$(APP) target_dbg/$(APP)_DEBUG target_rld/$(APP)_RELOAD
	ssh $(RPIP) $(RPOPTS) "PATH_REDPITAYA=/opt/redpitaya /boot/sbin/rw ; rm -rf /opt/redpitaya/www/apps/$(APP)/{index.html,js,css}"
	cd target/$(APP); scp $(RPSCP) -r index.html css js root@$(RPIP):/opt/redpitaya/www/apps/$(APP)/

upload_py: ./py/hugo.py
	ssh $(RPIP) $(RPOPTS) "PATH_REDPITAYA=/opt/redpitaya /boot/sbin/rw ; rm -rf /opt/redpitaya/www/apps/$(APP)/py/{data_dump.py,set.py,ver_mem.py,*.py}"
	scp $(RPSCP) ./py/*.py root@$(RPIP):/opt/redpitaya/www/apps/$(APP)/py/
	ssh $(RPIP) $(RPOPTS) "PATH_REDPITAYA=/opt/redpitaya /boot/sbin/rw ; chmod +x /opt/redpitaya/www/apps/$(APP)/py/*.py"
