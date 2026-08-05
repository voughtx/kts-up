// gogram_test — ISOLATED speed test (main system se alag)
// Download + upload timing via gogram (Go Pyrogram port)
package main

import (
	"bytes"
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/amarnathcjd/gogram/telegram"
)

func now() float64 { return float64(time.Now().UnixMilli()) / 1000.0 }

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
	chatID, _ := strconv.ParseInt(chatIDStr, 10, 64)
	msgID, _ := strconv.ParseInt(msgIDStr, 10, 32)

	client, err := telegram.NewClient(telegram.ClientConfig{
		AppID:         int32(apiID64),
		AppHash:       apiHash,
		StringSession: authString,
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
	fmt.Printf("[*] file size: %d MB\n", doc.Size/1024/1024)
	buf := bytes.NewBuffer(make([]byte, 0, doc.Size))
	t0 := now()
	if _, err := message.Download(&telegram.DownloadOptions{Buffer: buf}); err != nil {
		fmt.Fprintln(os.Stderr, "Download:", err)
		os.Exit(1)
	}
	t1 := now()
	dlt := t1 - t0
	fmt.Printf("[download] %d MB in %.1fs = %.2f MB/s\n", doc.Size/1024/1024, dlt, float64(doc.Size)/1024/1024/dlt)

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
	fmt.Printf("[upload] %d MB in %.1fs = %.2f MB/s\n", doc.Size/1024/1024, ult, float64(doc.Size)/1024/1024/ult)
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
	fmt.Printf("[done] download %.2f MB/s | upload %.2f MB/s\n", float64(doc.Size)/1024/1024/dlt, float64(doc.Size)/1024/1024/ult)
}
