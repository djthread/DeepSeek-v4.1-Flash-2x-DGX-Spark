# SPDX-License-Identifier: AGPL-3.0-only
"""CPU-only coverage of the MTU policy used by the candidate native build."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FastcommMtu(unittest.TestCase):
    @unittest.skipUnless(shutil.which('c++'), 'C++ compiler required')
    def test_peer_negotiation(self):
        source = r'''
#include "fastcomm_mtu.h"
#include <cassert>
#include <cstdint>
using ds41_fastcomm::negotiate_mtu;
int main() {
  // In particular, hardware max=4096 must not override active MTU=1024.
  static_assert(negotiate_mtu(3, 3) == 3);
  static_assert(negotiate_mtu(5, 3) == 3);
  static_assert(negotiate_mtu(3, 5) == 3);
  static_assert(negotiate_mtu(5, 5) == 5);
  for (uint32_t local = 1; local <= 5; ++local)
    for (uint32_t peer = 1; peer <= 5; ++peer) {
      auto mtu = negotiate_mtu(local, peer);
      assert(mtu == (local < peer ? local : peer));
      assert(mtu == negotiate_mtu(peer, local));
    }
  for (uint32_t invalid : {0u, 6u, UINT32_MAX})
    for (uint32_t valid = 1; valid <= 5; ++valid) {
      assert(negotiate_mtu(invalid, valid) == 0);
      assert(negotiate_mtu(valid, invalid) == 0);
    }
}
'''
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'test.cpp').write_text('#include <initializer_list>\n' + source)
            subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror',
                            '-I', str(ROOT / 'release/experimental/fastcomm'),
                            str(path / 'test.cpp'), '-o', str(path / 'test')], check=True)
            subprocess.run([str(path / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
