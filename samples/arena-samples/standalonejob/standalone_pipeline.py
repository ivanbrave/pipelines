#!/usr/bin/env python3
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import kfp
import arena
import kfp.dsl as dsl
import argparse

FLAGS = None

@dsl.pipeline(
  name='pipeline to run jobs',
  description='shows how to run pipeline jobs.'
)
def sample_pipeline(learning_rate=dsl.PipelineParam(name='learning_rate',
                            value='0.01'),
    dropout=dsl.PipelineParam(name='dropout',
                                  value='0.9'),
    model_version=dsl.PipelineParam(name='model_version', value='1')):
  """A pipeline for end to end machine learning workflow."""
  data="user-susan:/training"
  gpus="1"

  # 1. prepare data
  prepare_data = arena.StandaloneOp(
    name="prepare-data",
		image="byrnedo/alpine-curl",
    data=data,
		command="mkdir -p /training/dataset/mnist && \
  cd /training/dataset/mnist && \
  curl -O https://code.aliyun.com/xiaozhou/tensorflow-sample-code/raw/master/data/t10k-images-idx3-ubyte.gz && \
  curl -O https://code.aliyun.com/xiaozhou/tensorflow-sample-code/raw/master/data/t10k-labels-idx1-ubyte.gz && \
  curl -O https://code.aliyun.com/xiaozhou/tensorflow-sample-code/raw/master/data/train-images-idx3-ubyte.gz && \
  curl -O https://code.aliyun.com/xiaozhou/tensorflow-sample-code/raw/master/data/train-labels-idx1-ubyte.gz")
  # 2. prepare source code
  prepare_code = arena.StandaloneOp(
    name="source-code",
    image="alpine/git",
    data=data,
    command="mkdir -p /training/models/ && \
  cd /training/models/ && \
  if [ ! -d /training/models/tensorflow-sample-code ]; then git clone https://code.aliyun.com/xiaozhou/tensorflow-sample-code.git; else echo no need download;fi")

  # 3. train the models
  train = arena.StandaloneOp(
    name="train",
    image="tensorflow/tensorflow:1.11.0-gpu-py3",
    gpus=gpus,
    data=data,
    command="echo %s;echo %s;python /training/models/tensorflow-sample-code/tfjob/docker/mnist/main.py --max_steps 500 --data_dir /training/dataset/mnist --log_dir /training/output/mnist  --learning_rate %s --dropout %s" % (prepare_data.output, prepare_code.output, learning_rate, dropout),
    metric_name="Train-accuracy",
    metric_unit="PERCENTAGE",)
  # 4. export the model
  export_model = arena.StandaloneOp(
    name="export-model",
    image="tensorflow/tensorflow:1.11.0-py3",
    data=data,
    command="echo %s;python /training/models/tensorflow-sample-code/tfjob/docker/mnist/export_model.py --model_version=%s --checkpoint_path=/training/output/mnist /training/output/models" % (train.output, model_version))

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('--model_version', type=str,
                      default="1",
                      help='model version.')
  parser.add_argument('--dropout', type=str, default="0.9",
                      help='Keep probability for training dropout.')
  parser.add_argument('--learning_rate', type=str, default="0.001",
                      help='Initial learning rate.')
  FLAGS, unparsed = parser.parse_known_args()

  model_version = FLAGS.model_version
  dropout = FLAGS.dropout
  learning_rate = FLAGS.learning_rate

  EXPERIMENT_NAME="mnist"
  RUN_ID="run"
  KFP_SERVICE="ml-pipeline.kubeflow.svc.cluster.local:8888"
  import kfp.compiler as compiler
  compiler.Compiler().compile(sample_pipeline, __file__ + '.tar.gz')
  client = kfp.Client(host=KFP_SERVICE)
  try:
    experiment_id = client.get_experiment(experiment_name=EXPERIMENT_NAME).id
  except:
    experiment_id = client.create_experiment(EXPERIMENT_NAME).id
  run = client.run_pipeline(experiment_id, RUN_ID, __file__ + '.tar.gz',
                            params={'learning_rate':learning_rate,
                                     'dropout':dropout,
                                    'model_version':model_version})
