from setuptools import setup, find_packages

classifiers = ['Development Status :: Alpha',
               'Operating System :: POSIX :: Linux',
               'License :: OSI Approved :: MIT License',
               'Intended Audience :: Developers',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Topic :: Software Development',
               'Topic :: System :: Hardware']

setup(name='ST7789U_RPI',
      version='0.0.2',
      description='Library to control ST7789 TFT LCD displays. With or without CS Pin',
      long_description=open('README.md').read(),
      long_description_content_type='text/markdown',
      license='MIT',
      author='Oleksandr Soloviov',
      author_email='oleksolv@gmail.com',
      classifiers=classifiers,
      url='https://github.com/pimoroni/st7789-python/',
      packages=find_packages())
