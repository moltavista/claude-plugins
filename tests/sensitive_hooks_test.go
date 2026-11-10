package plugins_test

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestSensitiveConsumeHasSynchronousNativePrehook(t *testing.T) {
	for _, entry := range []string{"fab", "mstep"} {
		for _, runtime := range []string{"hooks.json", "codex-hooks.json"} {
			t.Run(entry+"/"+runtime, func(t *testing.T) {
				data, err := os.ReadFile(filepath.Join("..", "plugins", entry, "hooks", runtime))
				if err != nil {
					t.Fatal(err)
				}
				var config struct {
					Hooks map[string][]struct {
						Matcher string `json:"matcher"`
						Hooks   []struct {
							Command string   `json:"command"`
							Args    []string `json:"args"`
							Async   bool     `json:"async"`
							Timeout int      `json:"timeout"`
						} `json:"hooks"`
					} `json:"hooks"`
				}
				if err := json.Unmarshal(data, &config); err != nil {
					t.Fatal(err)
				}
				found := 0
				for _, group := range config.Hooks["PreToolUse"] {
					if group.Matcher != "^mcp__.+__decision_secret_consume$" {
						continue
					}
					for _, hook := range group.Hooks {
						if hook.Async || hook.Timeout != 5 {
							t.Fatal("consume may run before its bounded local protection completes")
						}
						if runtime == "codex-hooks.json" {
							if !strings.Contains(hook.Command, "hook pre-tool-use --agent codex --deliver") {
								t.Fatal("Codex consume does not use the local synchronous delivery handler")
							}
						} else if strings.Join(hook.Args, " ") != "hook pre-tool-use" || !strings.HasSuffix(hook.Command, "/scripts/fab-run") {
							t.Fatal("Claude consume does not invoke its native prehook")
						}
						found++
					}
				}
				if found != 1 {
					t.Fatalf("want one synchronous consume hook; got %d", found)
				}
			})
		}
	}
}

func TestSensitiveHookReleaseVersion(t *testing.T) {
	for _, entry := range []string{"fab", "mstep"} {
		for _, runtime := range []string{".claude-plugin", ".codex-plugin"} {
			data, err := os.ReadFile(filepath.Join("..", "plugins", entry, runtime, "plugin.json"))
			if err != nil {
				t.Fatal(err)
			}
			var manifest struct {
				Version string `json:"version"`
			}
			if json.Unmarshal(data, &manifest) != nil || manifest.Version != "0.9.0" {
				t.Errorf("%s/%s must ship as the current release, 0.9.0", entry, runtime)
			}
		}
	}
}
