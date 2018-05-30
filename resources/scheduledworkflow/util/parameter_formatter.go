// Copyright 2018 The Kubeflow Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

package util

import (
	"fmt"
	"regexp"
	"strings"
	"time"
)

const (
	scheduledTimeExpression = "[[ScheduledTime]]"
	currentTimeExpression   = "[[CurrentTime]]"
	IndexExpression         = "[[Index]]"
	scheduledTimePrefix     = "[[ScheduledTime."
	currentTimePrefix       = "[[CurrentTime."
	defaultTimeFormat       = "20060102150405"
	suffix                  = "]]"
)

// ParameterFormatter is an object that substitutes specific strings
// in workflow parameters by information about the workflow execution (time at
// which the workflow was started, time at which the workflow was scheduled, etc.)
type ParameterFormatter struct {
	scheduledEpoch int64
	nowEpoch       int64
	index          int64
}

func NewParameterFormatter(scheduledEpoch int64, nowEpoch int64,
	index int64) *ParameterFormatter {
	return &ParameterFormatter{
		scheduledEpoch: scheduledEpoch,
		nowEpoch:       nowEpoch,
		index:          index,
	}
}

func (p *ParameterFormatter) Format(s string) string {
	re := regexp.MustCompile(`\[\[(.*?)\]\]`)
	matches := re.FindAllString(s, -1)
	if matches == nil {
		return s
	}

	result := s

	for _, match := range matches {
		substitute := p.createSubtitute(match)
		result = strings.Replace(result, match, substitute, 1)
	}

	return result
}

func (p *ParameterFormatter) createSubtitute(match string) string {

	if strings.HasPrefix(match, scheduledTimeExpression) {
		return time.Unix(p.scheduledEpoch, 0).UTC().Format(defaultTimeFormat)
	} else if strings.HasPrefix(match, currentTimeExpression) {
		return time.Unix(p.nowEpoch, 0).UTC().Format(defaultTimeFormat)
	} else if strings.HasPrefix(match, IndexExpression) {
		return fmt.Sprintf("%v", p.index)
	} else if strings.HasPrefix(match, scheduledTimePrefix) {
		match = strings.Replace(match, scheduledTimePrefix, "", 1)
		match = strings.Replace(match, suffix, "", 1)
		return time.Unix(p.scheduledEpoch, 0).UTC().Format(match)
	} else if strings.HasPrefix(match, currentTimePrefix) {
		match = strings.Replace(match, currentTimePrefix, "", 1)
		match = strings.Replace(match, suffix, "", 1)
		return time.Unix(p.nowEpoch, 0).UTC().Format(match)
	} else {
		return match
	}
}
