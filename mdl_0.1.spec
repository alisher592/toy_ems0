# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['optimization.py'],
             pathex=[r'C:\\Users\Narynbaev\\Documents\\optimization.py'],
             binaries=[],
             datas=[('vcomp140.dll', '.')],
             hiddenimports=['pkg_resources.py2_warn','pyomo.common.plugins','pyomo.repn.util',
                            'pyomo.opt.plugins',
                            'pyomo.core.plugins',
                            'pyomo.dataportal.plugins',
                            'pyomo.duality.plugins',
                            'pyomo.checker.plugins',
                            'pyomo.repn.plugins',
                            'pyomo.pysp.plugins',
                            'pyomo.neos.plugins',
                            'pyomo.solvers.plugins',
                            'pyomo.gdp.plugins',
                            'pyomo.mpec.plugins',
                            'pyomo.dae.plugins',
                            'pyomo.bilevel.plugins',
                            'pyomo.scripting.plugins',
                            'pyomo.network.plugins',
                            'pandas._libs.skiplist',
                            'sklearn.utils._typedefs'
             ],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='module_0.2.1',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=True)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='module_0.2.1')
