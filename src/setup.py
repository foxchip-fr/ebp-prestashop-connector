from setuptools import setup, find_packages

setup(
    name='psebpconnector',
    version='1.0.6',
    url='https://github.com/foxchip-fr/ebp-prestashop-connector',
    author='Guillaume Chinal',
    author_email='contact@guillaumechinal.fr',
    description='Lightweight connector that synchronizes Prestashop orders with EBP Gestion Commerciale ',
    packages=find_packages(),
    install_requires=['O365 >= 2, < 3', 'requests >= 2, < 3'],
)