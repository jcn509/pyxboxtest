# WIP end-to-end test framework for Xbox software built with the [nxdk](https://github.com/XboxDev/nxdk)
Supports [XQEMU](https://github.com/xqemu/xqemu) and hopefully soon [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded). XQEMU may well be better, as it is unclear how well supported nxdk is with Cxbx-Reloaded. Cxbx-Reloaded support would be nice as with Cxbx-Reloaded (unlike with XQEMU) you do not need a copy of the BiOS or MCPX rom, and that would make it far easier to use and would mean you could run tests on CI platforms legally.

# Usage
This library is designed to be used with pytest, if you are not already familiair with pytest I suggest you read the [pytest documentation](https://docs.pytest.org) before continuing. After you have installed it you should add `pytest_plugins = ("pyxboxtest.pytest_plugin",)` to your conftest.py.

# Implemented
 - Running games/apps
 - Capturing kernel debug output
 - Controller input (uses Qemu's monitor rather than faking keyboard events so you can use your computer for other tasks without it interfering)
 - Screenshots
 - Headless mode so that you can run tests in the background without windows popping up

# TODO
## Definitely
- Support for HDD read/write (outside of Xbox apps)
  - Until there is a nice way to read/write HDD images on PC it will require either:
    - An app with FTP or some other protocol implemented running on XQEMU
      - Would be nice to provide a library that can be linked againts to allow this while your app is running
    - This may take the form of some extension to 
  - Some legal/opensource alternative to XBDM.dll
  - Some wrapper around fatxplorer or some other tool might be possible?
- Documentation
- Support for automated HDD copy/cleanup
  - Automatically copy a HDD image before an app is run so that the changes made won't affect other tests
  - To keep things efficient we can:
    - Use QEMU's copy on write drive creation feature

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