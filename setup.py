from setuptools import setup
from setuptools_rust import Binding, RustExtension

setup(
    name="aeryn-core-agent",
    version="0.1.0",
    packages=["aeryn_core"],
    rust_extensions=[RustExtension("aeryn_core.aeryn_native", binding=Binding.PyO3)],
    zip_safe=False,
)
