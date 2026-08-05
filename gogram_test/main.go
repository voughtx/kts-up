// gogram_test — ISOLATED speed test (main system se alag)
// Download + upload timing via gogram (Go Pyrogram port)
// KEY_19 (Pyrogram session) ko decode karke use karta hai (official example se)
package main

import (
	"bytes"
	"encoding/base64"
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/amarnathcjd/gogram/telegram"
)

func now() float64 { return float64(time.Now().UnixMilli()) / 1000.0 }

// dcIP — Telegram DC ID -> production IP (manual map, ResolveDataCenterIP naya version mein nahi)
func dcIP(dcID uint8) string {
	ips := map[uint8]string{
		1: "149.154.175.50",
		2: "149.154.167.51",
		3: "149.154.175.100",
		4: "149.154.167.91",
		5: "91.108.56.130",
	}
	if ip, ok := ips[dcID]; ok {
		return ip
	}
	return "149.154.175.50"
}

// decodePyrogramSessionString — Pyrogram string session -> gogram Session
// (official example: gogram/examples/sessions/pyrogram/main.go)
func decodePyrogramSessionString(encodedString string) (*telegram.Session, error) {
	const (
		dcIDSize     = 1 // uint8
		apiIDSize    = 4 // uint32
		testModeSize = 1 // bool (uint8)
		authKeySize  = 256
		userIDSize   = 8 // uint64
		isBotSize    = 1 // bool (uint8)
	)
	for len(encodedString)%4 != 0 {
		encodedString += "="
	}
	packedData, err := base64.URLEncoding.DecodeString(encodedString)
	if err != nil {
		return nil, fmt.Errorf("failed to decode base64 string: %w", err)
	}
	expectedSize := dcIDSize + apiIDSize + testModeSize + authKeySize + userIDSize + isBotSize
	if len(packedData) != expectedSize {
		return nil, fmt.Errorf("unexpected data length: got %d, want %d", len(packedData), expectedSize)
	}
	return &telegram.Session{
		Hostname: dcIP(uint8(packedData[0])),
		AppID:    int32(uint32(packedData[1])<<24 | uint32(packedData[2])<<16 | uint32(packedData[3])<<8 | uint32(packedData[4])),
		Key:      packedData[6 : 6+authKeySize],
	}, nil
}

func main() {
	apiIDStr := os.Getenv("API_ID")
	apiHash := os.Getenv("API_HASH")
	authString := os.Getenv("AUTH_STRING")
	chatIDStr := os.Getenv("CHAT_ID")
	msgIDStr := os.Getenv("MSG_ID")
	pubStr := os.Getenv("PUB")
	if apiIDStr == "" || apiHash == "" || authString == "" || chatIDStr == "" || msgIDStr == "" || pubStr == "" {
		fmt.Fprintln(os.Stderr, "missing env", errors.New("API_ID/API_HASH/AUTH_STRING/CHAT_ID/MSG_ID/PUB"))
		os.Exit(1)
	}
	apiID64, _ := strconv.ParseInt(apiIDStr, 10, 32)
	_ = apiID64 // session mein AppID already hai
	chatID, _ := strconv.ParseInt(chatIDStr, 10, 64)
	msgID, _ := strconv.ParseInt(msgIDStr, 10, 32)

	// decode Pyrogram session
	sess, err := decodePyrogramSessionString(authString)
	if err != nil {
		fmt.Fprintln(os.Stderr, "decode session:", err)
		os.Exit(1)
	}
	client, err := telegram.NewClient(telegram.ClientConfig{
		StringSession: sess.Encode(),
		MemorySession: true,
		DisableCache:  true,
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, "NewClient:", err)
		os.Exit(1)
	}
	if err := client.Connect(); err != nil {
		fmt.Fprintln(os.Stderr, "Connect:", err)
		os.Exit(1)
	}
	defer client.Disconnect()
	me, err := client.GetMe()
	if err != nil {
		fmt.Fprintln(os.Stderr, "GetMe:", err)
		os.Exit(1)
	}
	fmt.Printf("[*] connected as %s\n", me.Username)

	// download
	message, err := client.GetMessageByID(chatID, int32(msgID))
	if err != nil {
		fmt.Fprintln(os.Stderr, "GetMessageByID:", err)
		os.Exit(1)
	}
	doc := message.Document()
	if doc == nil {
		fmt.Fprintln(os.Stderr, "no document")
		os.Exit(1)
	}
	mb := float64(doc.Size) / 1024 / 1024
	fmt.Printf("[*] file size: %.0f MB\n", mb)
	buf := bytes.NewBuffer(make([]byte, 0, doc.Size))
	t0 := now()
	if _, err := message.Download(&telegram.DownloadOptions{Buffer: buf}); err != nil {
		fmt.Fprintln(os.Stderr, "Download:", err)
		os.Exit(1)
	}
	t1 := now()
	dlt := t1 - t0
	fmt.Printf("[download] %.0f MB in %.1fs = %.2f MB/s\n", mb, dlt, mb/dlt)

	// upload to pub channel
	target, err := client.ResolvePeer(pubStr)
	if err != nil {
		fmt.Fprintln(os.Stderr, "ResolvePeer:", err)
		os.Exit(1)
	}
	t2 := now()
	uploaded, err := client.UploadFile(buf.Bytes(), &telegram.UploadOptions{
		FileName: "gogram_test.bin",
	})
	if err != nil {
		fmt.Fprintln(os.Stderr, "UploadFile:", err)
		os.Exit(1)
	}
	t3 := now()
	ult := t3 - t2
	fmt.Printf("[upload] %.0f MB in %.1fs = %.2f MB/s\n", mb, ult, mb/ult)
	if _, err := client.MessagesSendMedia(&telegram.MessagesSendMediaParams{
		Peer: target,
		Media: &telegram.InputMediaUploadedDocument{
			File:     uploaded,
			MimeType: "application/octet-stream",
			Attributes: []telegram.DocumentAttribute{
				&telegram.DocumentAttributeFilename{FileName: "gogram_test.bin"},
			},
		},
		RandomID: telegram.GenerateRandomLong(),
	}); err != nil {
		fmt.Fprintln(os.Stderr, "Send:", err)
		os.Exit(1)
	}
	fmt.Printf("[done] download %.2f MB/s | upload %.2f MB/s\n", mb/dlt, mb/ult)
}
