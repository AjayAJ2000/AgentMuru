package catalog

import (
	"crypto/ed25519"
	_ "embed"
	"encoding/hex"

	"github.com/AjayAJ2000/AgentMuru/edge/internal/contracts"
)

//go:embed bootstrap-v1.json
var bootstrapData []byte

//go:embed bootstrap-v1.sig
var bootstrapSignature []byte

const bootstrapPublicKeyHex = "0bf90630848cc224fb0606edd6f092e57a8825aba45a48eb792867c2ca31ab4c"

func LoadBootstrap() (contracts.Catalog, error) {
	publicKey, err := hex.DecodeString(bootstrapPublicKeyHex)
	if err != nil {
		return contracts.Catalog{}, err
	}
	return Verify(bootstrapData, bootstrapSignature, ed25519.PublicKey(publicKey))
}
