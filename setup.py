from setuptools import find_packages, setup
from typing import List

def get_requirements() -> List[str]:
    requirements = []
    try:
        with open('requirements.txt', 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('-e'):
                    requirements.append(line)
    except FileNotFoundError:
        print("requirements.txt file not found. Make sure it exists!")
    return requirements

setup(
    name="BookMyDoctorAI",
    version="0.0.1",
    author="Sahil Rahate",
    author_email="sahilrahate567@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements(),
)