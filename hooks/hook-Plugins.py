#hook-Plugins.py

from PyInstaller.utils.hooks import collect_submodules
import plugins
print("Running hook for plugins...")

hiddenimports = collect_submodules("plugins")
hiddenimports += collect_submodules('Banwords')
hiddenimports += collect_submodules('BDunit')
hiddenimports += collect_submodules('Dungeon')
hiddenimports += collect_submodules('Finish')
hiddenimports += collect_submodules('Godcmd')
hiddenimports += collect_submodules('Hello')
hiddenimports += collect_submodules('Keyword')
hiddenimports += collect_submodules('LinkAI')
hiddenimports += collect_submodules('Role')
hiddenimports += collect_submodules('Tool')

print(f"Collected submodules: {hiddenimports}")
# hiddenimports = ['Godcmd','Dungeon','Role']
