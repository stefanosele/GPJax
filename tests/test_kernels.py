from gpjax import kernels
import jax.numpy as jnp
import pytest

from gpjax.kernels import RBF, cross_covariance, gram
from gpjax.parameters import initialise
from gpjax.utils import I


@pytest.mark.parametrize("dim", [1, 2, 5])
def test_gram(dim):
    x = jnp.linspace(-1.0, 1.0, num=10).reshape(-1, 1)
    if dim > 1:
        x = jnp.hstack([x] * dim)
    kern = RBF()
    params, _, _ = initialise(kern)
    gram_matrix = gram(kern, x, params)
    assert gram_matrix.shape[0] == x.shape[0]
    assert gram_matrix.shape[0] == gram_matrix.shape[1]


@pytest.mark.parametrize("n1", [3, 10, 20])
@pytest.mark.parametrize("n2", [3, 10, 20])
def test_cross_covariance(n1, n2):
    x1 = jnp.linspace(-1.0, 1.0, num=n1).reshape(-1, 1)
    x2 = jnp.linspace(-1.0, 1.0, num=n2).reshape(-1, 1)
    params, _, _ = initialise(RBF())
    kernel_matrix = cross_covariance(RBF(), x2, x1, params)
    assert kernel_matrix.shape == (n1, n2)


def test_call():
    kernel = RBF()
    params, _, _ = initialise(kernel)
    x, y = jnp.array([[1.0]]), jnp.array([[0.5]])
    point_corr = kernel(x, y, params)
    assert isinstance(point_corr, jnp.DeviceArray)
    assert point_corr.shape == ()


@pytest.mark.parametrize("dim", [1, 2, 5])
@pytest.mark.parametrize(
    "ell, sigma", [(0.1, 0.1), (0.5, 0.1), (0.1, 0.5), (0.5, 0.5)]
)
def test_pos_def(dim, ell, sigma):
    n = 30
    x = jnp.linspace(0.0, 1.0, num=n).reshape(-1, 1)
    if dim > 1:
        x = jnp.hstack((x) * dim)
    kern = RBF()
    params = {"lengthscale": jnp.array([ell]), "variance": jnp.array(sigma)}

    gram_matrix = gram(kern, x, params)
    jitter_matrix = I(n) * 1e-6
    gram_matrix += jitter_matrix
    min_eig = jnp.linalg.eigvals(gram_matrix).min()
    assert min_eig > 0


@pytest.mark.parametrize("dim", [1, 2, 5, 10])
def test_initialisation(dim):
    kern = RBF(ndims=dim)
    params, _, _ = initialise(kern)
    assert list(params.keys()) == ["lengthscale", "variance"]
    assert all(params["lengthscale"] == jnp.array([1.0] * dim))
    assert params["variance"] == jnp.array([1.0])
    if dim > 1:
        assert kern.ard
    else:
        assert not kern.ard


def test_dtype():
    params, _, _ = initialise(RBF())
    for k, v in params.items():
        assert v.dtype == jnp.float64
