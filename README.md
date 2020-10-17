# WIP end-to-end test framework for Xbox software built with the [nxdk](https://github.com/XboxDev/nxdk)
Supports [XQEMU](https://github.com/xqemu/xqemu) and hopefully soon [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded). XQEMU may well be better, as it is unclear how well supported nxdk is with Cxbx-Reloaded. Cxbx-Reloaded support would be nice as with Cxbx-Reloaded (unlike with XQEMU) you do not need a copy of the BiOS or MCPX rom, and that would make it far easier to use and would mean you could run tests on CI platforms legally.

# Usage
This library is designed to be used with pytest, if you are not already familiair with pytest I suggest you read the [pytest documentation](https://docs.pytest.org) before continuing. After you have installed it you should add `pytest_plugins = ("pyxboxtest.pytest_plugin",)` to your conftest.py.

An extra command line argument `--headless` may be passed to pytest to tell it to execute the tests in headless mode (no XQEMU window is visible when running the tests). This is nice if you want to run tests in the background whilst you do something else and it may be faster.

Any HDD images generated during test runs will by default be stored in a "pytest-NUM" directory in your systems temporary directory (in a subdirectory like xqemu_hdd_images) to change that you can use `--basetemp=mydir` when running pytest, but be careful as the contents of `mydir` will be erased! See the [docs](https://pytest.org/en/latest/tmpdir.html#the-default-base-temporary-directory) for more details.

Keep HDD image file names relatively short to avoid issues with filenames that are too long.
Make sure to give any HDD template fixtures session scope to avoid needless copies! On instantiation of very HDD template generator the base image is copied and any needed changes are made so don't instantiate any that you don't plan to use as its slow. This may change in the future in order to allow intermediate templates without the overhead!

You may have issues if you try and instantiate globally, I suggest only doing so in a test/function/fixture (IMO in almost every situation you should be using a fixture and not a global variable anyway).

In order to run the tests in this repo (i.e. the unit tests for the framework itself), you do not need to have XQEMU installed but you do need qemu-img (which is installed as part of QEMU).

Document HDD copy/cleanup - fast using COW and only doing it when necessary. Strongly discourage ever using an HDD image directly

# Features
 - Running games/apps
 - Capturing kernel debug output
 - Controller input (uses Qemu's monitor rather than faking keyboard events so you can use your computer for other tasks without it interfering)
 - Screenshots
 - Headless mode so that you can run tests in the background without windows popping up

# TODO
## Definitely
- Refactor the FTP connection code. Instead accept a list of ports (and IPs??) that should be forwarded to *some other port* then we capture any network traffic we want. Will need to provide an example of this for FTP.
- Support for HDD read/write (outside of Xbox apps)
  - Implementation uses an Xbox app running an FTP server (there is an easy to use wrapper around this)
- Documentation
- Safe parallel test execution
  - Need to ensure that xqemu ports are selected and then used atomically
  - Need to ensure that new HDD file names are selected atomically

## If time allows
- Pause/continue execution using QEMU's monitor
- Investigate https://github.com/mborgerson/xqemu-kernel. I couldn't get it to work :/ but if it could be used it would provide a way to run tests legally on some CI platform (currently tricky due to legal issues with the kernel)
- Support for Cxbx-Reloaded (tests should work regardless of which emulator is used, without much modification)
  - Currently NXDK support is not very good, so this may not happen for some time
  - May not be possible to support:
    - headless mode
    - sending fake inputs to the app without generating fake keyboard input that would potentially interfere with other applications
    - screenshots that are not affected by the size of the window
      - May not be an issue if window size is the same as the Xbox's resolution by default

## Once everthing else is done
- Investigate support for qemu monitor based debugging
  - [xboxpy](https://github.com/XboxDev/xboxpy) will work __today__ so long as it works with XQEMU. We may be able to do some additional debugging using XQEMU's monitor without the overhead of debug libraries or XBDM.dll
- Investigate support for running tests on real hardware. Should be possible using (some legal alternative to) XBDM.dll to control the xbox, but there are some challenges to overcome such as faking controller input and loading HDD setup quickly.