try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='DeepLabChop',
      description='Learning exercise reimplementing DeepLabCut tools for markerless tracking of behaving animals.',
      author='Ronny Eichler',
      author_email='ronny.eichler@gmail.com',
      version='0.0.1',
      packages=['deeplabchop'],
      entry_points="""[console_scripts]
            dlc=dlc:main""")
