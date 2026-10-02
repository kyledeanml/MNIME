import sys, os
base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
print('base:', base_path)
print('dist/MNIME exists:', os.path.exists(os.path.join(base_path, 'dist', 'MNIME')))
print('list dist:', os.listdir(os.path.join(base_path, 'dist')) if os.path.exists(os.path.join(base_path, 'dist')) else 'no dist')
