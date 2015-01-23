import os.path

cur_dir = os.path.dirname(__file__)
if not cur_dir:
  cur_dir = '.'
keywords = set()
for fname in os.listdir(cur_dir):
  if fname.endswith('.txt'):
    with open(os.path.join(cur_dir, fname)) as f:
      new_keywords = f.read().split()
      keywords.update(k.lower() for k in new_keywords)

print '\n'.join('\\item {}'.format(kw.replace('_', '\\_')) for kw in sorted(keywords))

