from setuptools import setup, find_packages

setup(
    name="mygit", version="0.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["click==7.1.2"],
    entry_points='''
        [console_scripts]
        mygit=app.main:cli
    '''
)
