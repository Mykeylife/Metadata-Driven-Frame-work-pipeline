import os
import sys

# Forces the root folder and inner package namespaces into the evaluation path
root_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

pipeline_dir = os.path.join(root_dir, "pipeline")
if os.path.exists(pipeline_dir) and pipeline_dir not in sys.path:
    sys.path.insert(1, pipeline_dir)
