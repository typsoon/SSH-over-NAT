# Maintainer: Your Name <you@example.com>
pkgname=python-ssh-over-nat
pkgver=1.0.0 # you can set dynamic version fetching later
pkgrel=1
proj_name=SSH-over-NAT
pkgdesc="SSH-over-NAT tool using NAT-traversal techniques"
arch=('any')
repoaddr=https://github.com/typsoon/SSH-over-NAT
url="$repoaddr"
license=('MIT')
depends=('python' 'python-requests' 'python-psutil' 'python-pydantic' 'python-platformdirs' 'python-doit')
makedepends=('python-setuptools' 'python-build' 'python-wheel' 'git' 'python-pip')
source=("$proj_name::git+$repoaddr.git#branch=main")
sha256sums=('SKIP') # Use SKIP for VCS source

build() {
  cd "$srcdir/$proj_name"
  python -m build --wheel --no-isolation
}

package() {
  cd "$srcdir/$proj_name"

  python -m pip install --root-user-action=ignore --root="$pkgdir" --no-deps --ignore-installed dist/*.whl

  # Optional: install README
  install -Dm644 README.md "$pkgdir/usr/share/doc/$pkgname/README.md"
}
