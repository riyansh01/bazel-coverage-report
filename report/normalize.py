# Copyright 2018 The Bazel Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from report import go

class SourceFilenameNormalizer:
  def __init__(self, go_importmap = None, java_paths = None, workspace_name = None, dest_dir = None):
    self.go_importmap = go_importmap
    self.java_paths = java_paths
    self.dest_dir = dest_dir
    self.workspace_name = workspace_name

  def warning(self, s):
    print("NORMALIZATION WARNING: " + s)

  def normalize_source_filename(self, fn):
    if fn.endswith(".go"):
      if not self.go_importmap:
        raise Exception(
          "cannot normalize *.go source file names since no " +
          "go_importmap was provided")
      for prefix in self.go_importmap:
        if fn.startswith(prefix):
          return self.go_importmap[prefix] + fn[len(prefix):]
      return fn
    elif fn.endswith(".java"):
      if not self.java_paths:
        raise Exception(
          "cannot normalize *.java source file names since no " +
          "java_paths was provided")
      full_path = None
      for root in self.java_paths:
        p = os.path.join(root, fn)
        if os.path.exists(p):
          if full_path:
            self.warning(
              ("%s can match at least two files: %s and %s: " +
              "cannot normalize") % (
                fn,
                full_path,
                p))
            return fn
          full_path = p
      if not full_path:
        p = os.path.join(self.dest_dir, self.workspace_name, fn)
        if os.path.exists(p):
          return p
        self.warning("%s does not belong to any java_path; java_paths: %s" % (
          fn,
          ', '.join(self.java_paths)
        ))
        return fn
      return os.path.relpath(full_path, self.dest_dir)
    else:
      return fn

  def normalize_coverage_dat(self, cov):
    if len(cov) == 0:
      return []

    if cov[0].startswith("mode: "):
      # We assume this is a coverage report generated by rules_go
      # in Go's coverprofile format.
      cov = go.Coverprofile(cov).to_lcov()

    res = []
    has_records = False
    for line in cov:
      if line.startswith("SF:"):
        res.append(
          "SF:" + 
          self.normalize_source_filename(line[len("SF:"):].strip()))
      else:
        if line.startswith("DA:") or line.startswith("FNDA:"):
          has_records = True
        res.append(line)

    if not has_records:
      return []    
    return res