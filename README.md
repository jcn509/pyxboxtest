# WIP [XQEMU](https://github.com/xqemu/xqemu)-based end-to-end test framework for Xbox software built with the [nxdk](https://github.com/XboxDev/nxdk)
# Build status
![pyxboxtest](https://github.com/jcn509/pyxboxtest/workflows/pyxboxtest/badge.svg)

# Usage
This library is designed to be used with pytest, if you are not already familiair with pytest I suggest you read the [pytest documentation](https://docs.pytest.org) before continuing. After you have installed it you should add `pytest_plugins = ("pyxboxtest.pytest_plugin",)` to your conftest.py.

An extra command line argument `--headless` may be passed to pytest to tell it to execute the tests in headless mode (no XQEMU window is visible when running the tests). This is nice if you want to run tests in the background whilst you do something else and it may be faster.

You need to supply the paths to an mcpx rom and and xqemu compatible Xbox bios using the `--bios` and `--mcpx-rom` command line arguments. Note: if you don't want to specify these every time then you can set them in your pytest.ini using [addopts](https://docs.pytest.org/en/stable/reference.html#confval-addopts).

Any HDD images generated during test runs will by default be stored in a "pytest-NUM" directory in your systems temporary directory (in a subdirectory like xqemu_hdd_images). Pytest will create a new folder for each run and will delete the old ones after a certain number of runs. To change where they are stored you can use `--basetemp=mydir` when running pytest, but be careful as the contents of `mydir` will be erased! See the [pytest docs](https://pytest.org/en/latest/tmpdir.html#the-default-base-temporary-directory) for more details.

Keep HDD image file names relatively short to avoid issues with filenames that are too long.
Make sure to give any HDD template fixtures session scope to avoid needless copies! On instantiation of every HDD template generator the base image is (COW) copied and any needed changes are made so don't instantiate any that you don't plan to use it. This really shouldn't be an issue as there is no good reason to make a template that you don't use... You may have issues if you try and instantiate HDD templates globally, I suggest only doing so in a test/function/fixture (IMO in almost every situation you should be using a fixture and not a global variable anyway).

In order to run the tests in this repo (i.e. the unit tests for the framework itself), you do not need to have XQEMU installed but you do need qemu-img (which is installed as part of QEMU).

Creating HDDs using templates is fast and space efficient as it only create a COW (copy on write) copy. I would reccomend that you always generate a fresh HDD from a template to avoid changes to a HDD during a test affecting other tests or future test runs.

Until I clean up this readme and write some proper docs, you can see some sample tests in the sample_tests folder.

# Features
- Running games/apps
- Capturing kernel debug output
- Automated controller input (uses Qemu's monitor rather than faking keyboard events so you can use your computer for other tasks without it interfering)
- Screenshots (using Qemu's monitor so that they are unaffected by Window size or headless mode)
- Headless mode so that you can run tests in the background without windows popping up
- Network connections e.g. FTP can be forwarded
- Setup HDD image templates from which you can create clean images to be used for your tests
  - Prevents changes to a HDD from affecting other tests in the current run (and future runs too)
  - You can use an existing HDD image to form the basis of the template
  - Copy On Write copies of the template are created rather than full copies to save on storage space and time whilst still ensuring test isolation
  - You can make modifications to HDDs in a programmatic way by specifying the changes that should be made to a templates input image
    - You can create sub-templates from existing templates where you only need to specify any additional changes that you would like
  - There is no need to delete the new copies after the test as pytest will clean them up in the future
  - pyxboxtest ships with a built in completely blank image from which you can create new templates

# TODO
- Refactor the FTP connection code. Instead accept a list of ports (and IPs??) that should be forwarded to *some other port* then we capture any network traffic we want. Will need to provide an example of this for FTP.
- Support for HDD read/write (outside of Xbox apps)
  - Implementation uses an Xbox app running an FTP server (there is an easy to use wrapper around this)
- Documentation
- Safe parallel test execution
  - Need to ensure that xqemu ports are selected and then used atomically
  - Need to ensure that new HDD file names are selected atomically
    - May not be an issue as I believe pytest will automatically put them in new folders?
- Get the package listed on PyPi
- Add a "stock" built in HDD image that has TDATA/UDATA/whatever else a game/app might expect that isn't copyrighted
- Logging
- Ability to throw away all unread KD data (makes it easier to get the latest lines)
  -  Need to update controller sample test once this is done

# Possible extensions/useful tools
- Pause/continue execution using QEMU's monitor
- Investigate https://github.com/mborgerson/xqemu-kernel. I couldn't get it to work :/ but if it could be used it would provide a way to run tests legally on some CI platform (currently tricky due to legal issues with the kernel)
- Support for [Cxbx-Reloaded](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded) (tests should work regardless of which emulator is used, without much modification)
  - Currently [NXDK support does not seem to be very good](https://github.com/Cxbx-Reloaded/Cxbx-Reloaded/issues/1562), so this may not be worth the effort
  - Cxbx-Reloaded support would be nice as with Cxbx-Reloaded (unlike with XQEMU) you do not need a copy of the BiOS or MCPX rom, and that would make it far easier to use and would mean you could run tests on CI platforms legally.
    - This may become irrelevant with projects like a [homebrew Xbox kernel based on react OS](https://reactos.org/wiki/Run_Xbox_Games_on_ReactOS) or something like [xqemu-kernel](https://github.com/mborgerson/xqemu-kernel)
    - May not be possible to support:
      - headless mode
      - sending fake inputs to the app without generating fake keyboard input that would potentially interfere with other applications
      - screenshots that are not affected by the size of the window
        - May not be an issue if window size is the same as the Xbox's resolution by default
- Investigate support for qemu monitor based debugging
  - [xboxpy](https://github.com/XboxDev/xboxpy) will work __today__ so long as it works with XQEMU. We may be able to do some additional debugging using XQEMU's monitor without the overhead of debug libraries or XBDM.dll
- See what can be done with [pyrebox](https://pyrebox.readthedocs.io/en/latest)
- See what can be done with [libvirt](https://libvirt.org)
- Investigate support for running tests on real hardware. Should be possible using (some legal alternative to) XBDM.dll to control the xbox, but there are some challenges to overcome such as faking controller input and loading HDD setup quickly.
- Image comparrison:
  - https://github.com/Apkawa/pytest-image-diff/
  - https://github.com/olymk2/pytest-inomaly
- Text extraction from screenshots:
  - https://pypi.org/project/pytesseract/

# Development
Pipenv is used to manage the dev environment, whilst setup.py is used to allow installing the library from pip. Please only add packages to the Pipfile and then sync them to the setup.py using `pipenv-setup sync --pipfile`, there is a CI check to make sure that they stay in sync. In the future this process may be automated instead. Please make sure that you install dependencies that are only needed to test the pyxboxtest library as dev dependencies.