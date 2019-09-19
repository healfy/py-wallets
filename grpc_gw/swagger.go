package main

import (
	"io/ioutil"

	"github.com/pkg/errors"
)

func readSwaggerJSON(path string) ([]byte, error) {
	data, err := ioutil.ReadFile(path)
	if err != nil {
		return []byte{}, errors.Wrap(err, "cannot read swagger file")
	}
	return data, nil
}
