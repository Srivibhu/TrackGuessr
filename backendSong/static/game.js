// ===========================================================
// GAME STATE
// ===========================================================
let score = 0;
let currentMode = null;

let currentSong = null;
let currentSongList = [];

let playStartTime = null;
let accumulatedPlayMs = 0;

const FADE_MS = 360;
let loadingInterval = null;
let currentStreak = 0;

// High scores per mode (local)
let highScores = {
    top: 0,
    global: 0
};

// Leaderboard entries (local only)
let leaderboardEntries = [];

// ===========================================================
// ELEMENTS
// ===========================================================
const genreSelectionDiv = document.getElementById("genre-selection");
const gameAreaDiv = document.getElementById("game-area");

const scoreDisplay = document.getElementById("score");
const feedback = document.getElementById("feedback");
const streakDisplay = document.getElementById("streak");

const audioPlayer = document.getElementById("audio-player");
const playBtn = document.getElementById("play-audio-btn");
const nextSongBtn = document.getElementById("next-song-btn");
const backToMenuBtn = document.getElementById("back-to-menu-btn");

const spotifyLoginBtn = document.getElementById("spotify-login-btn");
const spotifyLogoutBtn = document.getElementById("spotify-logout-btn");

const themeToggleBtn = document.getElementById("theme-toggle-btn");

const userInfoPanel = document.getElementById("user-info");
const userNameEl = document.getElementById("user-name");
const userAvatarEl = document.getElementById("user-avatar");

const songImageEl = document.getElementById("song-image");
const songTitleEl = document.getElementById("song-title");
const songArtistEl = document.getElementById("song-artist");

const optionsContainer = document.getElementById("options-container");

const highscoreTopEl = document.getElementById("highscore-top");
const highscoreGlobalEl = document.getElementById("highscore-global");
const leaderboardListEl = document.getElementById("leaderboard-list");
const loadingPanel = document.getElementById("loading-panel");
const loadingProgress = document.getElementById("loading-progress");
const gameContent = document.getElementById("game-content");

// Detect backend URL: local dev vs deployed
const BACKEND_BASE =
    window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:5000"
        : "https://trackguessr.onrender.com"; // replace with real Render URL

// ===========================================================
// SCREEN TRANSITIONS
// ===========================================================
function hideScreen(el) {
    if (!el) return;
    el.classList.add("is-hidden");
    el.setAttribute("aria-hidden", "true");
    window.setTimeout(() => {
        if (el.classList.contains("is-hidden")) {
            el.classList.add("is-gone");
            el.style.display = "none";
        }
    }, FADE_MS);
}

function showScreen(el) {
    if (!el) return;
    el.style.display = "block";
    el.classList.remove("is-gone");
    window.requestAnimationFrame(() => {
        el.classList.remove("is-hidden");
    });
    el.setAttribute("aria-hidden", "false");
}

function showLoading() {
    if (loadingPanel) {
        loadingPanel.classList.remove("is-hidden");
        loadingPanel.style.display = "grid";
    }
    if (gameContent) {
        gameContent.style.display = "none";
    }
    if (loadingProgress) {
        loadingProgress.style.width = "0%";
    }

    let progress = 0;
    if (loadingInterval) {
        window.clearInterval(loadingInterval);
    }
    loadingInterval = window.setInterval(() => {
        progress = Math.min(90, progress + Math.random() * 12);
        if (loadingProgress) {
            loadingProgress.style.width = `${Math.floor(progress)}%`;
        }
    }, 260);
}

function hideLoading() {
    if (loadingInterval) {
        window.clearInterval(loadingInterval);
        loadingInterval = null;
    }
    if (loadingProgress) {
        loadingProgress.style.width = "100%";
    }
    window.setTimeout(() => {
        if (loadingPanel) {
            loadingPanel.classList.add("is-hidden");
            loadingPanel.style.display = "none";
        }
        if (gameContent) {
            gameContent.style.display = "grid";
        }
    }, 240);
}

function flashFeedback(type) {
    const body = document.body;
    const successClass = "flash-success";
    const errorClass = "flash-error";
    body.classList.remove(successClass, errorClass);
    body.classList.add(type === "success" ? successClass : errorClass);
    window.setTimeout(() => {
        body.classList.remove(successClass, errorClass);
    }, 220);
}

function playFeedbackTone(type) {
    try {
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const osc = context.createOscillator();
        const gain = context.createGain();
        osc.type = "sine";
        osc.frequency.value = type === "success" ? 740 : 220;
        gain.gain.value = 0.12;
        osc.connect(gain);
        gain.connect(context.destination);
        osc.start();
        osc.stop(context.currentTime + 0.12);
        osc.onended = () => context.close();
    } catch (e) {
        // Ignore audio failures
    }
}

// ===========================================================
// THEME
// ===========================================================
function applyTheme(mode) {
    document.documentElement.classList.toggle("dark", mode === "dark");
    if (themeToggleBtn) {
        themeToggleBtn.textContent = mode === "dark" ? "Light mode" : "Dark mode";
    }
}

// ===========================================================
// HIGHSCORES + LEADERBOARD
// ===========================================================
function loadHighScores() {
    try {
        const raw = localStorage.getItem("trackGuessrHighScores");
        if (raw) {
            const parsed = JSON.parse(raw);
            if (parsed && typeof parsed === "object") {
                highScores = { ...highScores, ...parsed };
            }
        }
    } catch (e) {
        console.warn("Failed to load highscores", e);
    }

    try {
        const rawLb = localStorage.getItem("trackGuessrLeaderboard");
        if (rawLb) {
            const parsed = JSON.parse(rawLb);
            if (Array.isArray(parsed)) {
                leaderboardEntries = parsed;
            }
        }
    } catch (e) {
        console.warn("Failed to load leaderboard", e);
    }

    updateHighscoreDisplay();
    updateLeaderboardUI();
}

function saveHighScores() {
    try {
        localStorage.setItem("trackGuessrHighScores", JSON.stringify(highScores));
    } catch (e) {
        console.warn("Failed to save highscores", e);
    }
}

function saveLeaderboard() {
    try {
        localStorage.setItem("trackGuessrLeaderboard", JSON.stringify(leaderboardEntries));
    } catch (e) {
        console.warn("Failed to save leaderboard", e);
    }
}

function updateHighscoreDisplay() {
    if (highscoreTopEl) {
        highscoreTopEl.textContent = `Best: ${highScores.top || 0} pts`;
    }
    if (highscoreGlobalEl) {
        highscoreGlobalEl.textContent = `Best: ${highScores.global || 0} pts`;
    }
}

function updateLeaderboardUI() {
    if (!leaderboardListEl) return;

    leaderboardListEl.innerHTML = "";

    if (!leaderboardEntries.length) {
        const li = document.createElement("li");
        li.className = "leaderboard-empty";

        const title = document.createElement("div");
        title.className = "leaderboard-empty-title";
        title.textContent = "No scores yet";

        const bars = document.createElement("div");
        bars.className = "leaderboard-empty-bars";

        for (let i = 0; i < 3; i += 1) {
            const bar = document.createElement("div");
            bar.className = "leaderboard-empty-bar";
            bars.appendChild(bar);
        }

        li.appendChild(title);
        li.appendChild(bars);
        leaderboardListEl.appendChild(li);
        return;
    }

    leaderboardEntries
        .slice(0, 10)
        .forEach((entry, index) => {
            const li = document.createElement("li");

            const left = document.createElement("span");
            left.textContent = `${index + 1}. ${entry.score} pts`;

            const right = document.createElement("span");
            right.className = "leaderboard-mode";
            const modeLabel = entry.mode === "global" ? "Global Hits" : "Top Tracks";
            right.textContent = modeLabel;

            li.appendChild(left);
            li.appendChild(right);
            leaderboardListEl.appendChild(li);
        });
}

function recordScoreToLeaderboard() {
    if (!currentMode) return;

    leaderboardEntries.push({
        mode: currentMode,
        score,
        ts: Date.now()
    });

    leaderboardEntries.sort((a, b) => b.score - a.score);
    leaderboardEntries = leaderboardEntries.slice(0, 10);

    saveLeaderboard();
    updateLeaderboardUI();
}

function finalizeRunHighscore() {
    if (!currentMode) return;
    const prevBest = highScores[currentMode] || 0;
    if (score > prevBest) {
        highScores[currentMode] = score;
        saveHighScores();
        updateHighscoreDisplay();
    }
}

// ===========================================================
// AUTH UI (using /auth/status)
// ===========================================================
function showLoggedOutUI() {
    if (spotifyLoginBtn) spotifyLoginBtn.style.display = "inline-flex";
    if (spotifyLogoutBtn) spotifyLogoutBtn.style.display = "none";
    if (userInfoPanel) userInfoPanel.style.display = "none";
}

function showLoggedInUI(data) {
    if (spotifyLoginBtn) spotifyLoginBtn.style.display = "none";
    if (spotifyLogoutBtn) spotifyLogoutBtn.style.display = "inline-flex";
    if (userInfoPanel) userInfoPanel.style.display = "flex";

    const name = data.display_name || data.id || "Spotify user";

    if (userNameEl) {
        userNameEl.textContent = name;
    }

    const avatar = data.image_url || "";
    if (userAvatarEl) {
        userAvatarEl.src = avatar || "data:image/gif;base64,R0lGODlhAQABAAAAACw=";
    }
}

async function refreshAuthUI() {
    try {
        const res = await fetch(BACKEND_BASE + "/auth/status", {
            credentials: "include"
        });

        if (!res.ok) {
            showLoggedOutUI();
            return;
        }

        const data = await res.json();
        if (!data.logged_in) {
            showLoggedOutUI();
            return;
        }

        showLoggedInUI(data);
    } catch (err) {
        console.warn("Failed to fetch /auth/status", err);
        showLoggedOutUI();
    }
}

// ===========================================================
// INITIALIZE
// ===========================================================
async function initializeGame() {
    const welcomeScreen = document.getElementById("welcome-screen");

    const seenSplash = localStorage.getItem("trackGuessrSeenSplash") === "1";

    if (welcomeScreen) {
        if (seenSplash) {
            welcomeScreen.classList.add("is-hidden", "is-gone");
            welcomeScreen.style.display = "none";
            welcomeScreen.setAttribute("aria-hidden", "true");
        } else {
            welcomeScreen.addEventListener("click", () => {
                hideScreen(welcomeScreen);
                localStorage.setItem("trackGuessrSeenSplash", "1");
            });
        }
    }

    loadHighScores();

    let savedTheme = localStorage.getItem("theme");
    if (!savedTheme) {
        savedTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    }
    applyTheme(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener("click", () => {
            const now = document.documentElement.classList.contains("dark")
                ? "dark"
                : "light";
            const next = now === "dark" ? "light" : "dark";
            applyTheme(next);
            localStorage.setItem("theme", next);
        });
    }

    if (spotifyLoginBtn) {
        spotifyLoginBtn.addEventListener("click", () => {
            window.location.href = BACKEND_BASE + "/login";
        });
    }
    if (spotifyLogoutBtn) {
        spotifyLogoutBtn.addEventListener("click", () => {
            window.location.href = BACKEND_BASE + "/logout";
        });
    }

    await refreshAuthUI();

    document.querySelectorAll(".genre-btn[data-mode]").forEach(btn => {
        btn.addEventListener("click", () => {
            startMode(btn.dataset.mode);
        });
    });

    if (backToMenuBtn) {
        backToMenuBtn.addEventListener("click", resetToMenu);
    }

    if (playBtn) {
        playBtn.addEventListener("click", () => {
            if (playBtn.disabled) return;

            if (audioPlayer.paused) {
                audioPlayer.play().then(() => {
                    if (!playStartTime) playStartTime = performance.now();
                    playBtn.textContent = "Pause";
                }).catch(err => {
                    console.warn("Playback failed:", err);
                });
            } else {
                audioPlayer.pause();
                if (playStartTime) {
                    accumulatedPlayMs += performance.now() - playStartTime;
                    playStartTime = null;
                }
                playBtn.textContent = "Play";
            }
        });
    }

    audioPlayer.addEventListener("ended", () => {
        if (playStartTime) {
            accumulatedPlayMs += performance.now() - playStartTime;
            playStartTime = null;
        }
        if (playBtn) playBtn.textContent = "Play";
    });

    if (nextSongBtn) {
        nextSongBtn.addEventListener("click", loadSong);
    }

    if (scoreDisplay) scoreDisplay.textContent = "Score: 0";
    if (streakDisplay) streakDisplay.textContent = "Streak: 0";
    if (feedback) feedback.textContent = "Choose a mode to begin.";
}

// ===========================================================
// START MODE
// ===========================================================
async function startMode(mode) {
    currentMode = mode;
    score = 0;
    currentStreak = 0;

    if (scoreDisplay) scoreDisplay.textContent = "Score: 0";
    if (streakDisplay) streakDisplay.textContent = "Streak: 0";
    if (feedback) {
        feedback.textContent = "Loading...";
        feedback.style.color = "";
    }

    hideScreen(genreSelectionDiv);
    showScreen(gameAreaDiv);
    showLoading();

    const endpoint =
        mode === "top"
            ? "/api/quiz/top-tracks"
            : "/api/quiz/global-hits";

    try {
        const response = await fetch(BACKEND_BASE + endpoint, {
            credentials: "include",
        });

        const data = await response.json();

        if (!response.ok || !data.questions) {
            hideLoading();
            if (feedback) {
                feedback.textContent = "Error contacting backend.";
                feedback.style.color = "#e74c3c";
            }
            return;
        }

        const questions = data.questions;
        if (!Array.isArray(questions) || !questions.length) {
            hideLoading();
            if (feedback) {
                feedback.textContent = "No tracks available for this mode.";
                feedback.style.color = "#e74c3c";
            }
            return;
        }

        const songs = questions.map((q, i) => ({
            id: 1000 + i,
            title: q.correct,
            artist: q.artist,
            audioFile: q.audio_url,
            options: Array.isArray(q.options) ? q.options : [q.correct],
            imageFile: q.image
        }));

        startGameWithSongs(songs);
    } catch (err) {
        console.error("startMode error:", err);
        hideLoading();
        if (feedback) {
            feedback.textContent = "Error contacting backend.";
            feedback.style.color = "#e74c3c";
        }
    }
}

// ===========================================================
// BEGIN ROUND
// ===========================================================
function startGameWithSongs(songs) {
    currentSongList = songs.slice();

    hideLoading();

    loadSong();
}

// ===========================================================
// LOAD SONG
// ===========================================================
function loadSong() {
    if (!currentSongList || currentSongList.length === 0) {
        finalizeRun();
        return;
    }

    accumulatedPlayMs = 0;
    playStartTime = null;

    currentSong = currentSongList.shift();

    if (songImageEl) {
        songImageEl.src = currentSong.imageFile || "";
    }
    if (songTitleEl) songTitleEl.textContent = "";
    if (songArtistEl) songArtistEl.textContent = currentSong.artist || "";

    if (optionsContainer) {
        optionsContainer.innerHTML = "";

        const shuffled = shuffleArray(currentSong.options);

        shuffled.forEach(option => {
            const btn = document.createElement("button");
            btn.className = "option-btn";
            btn.textContent = option;

            btn.addEventListener("click", () => {
                handleGuess(option === currentSong.title, btn);
            });

            optionsContainer.appendChild(btn);
        });
    }

    audioPlayer.src = currentSong.audioFile || "";
    if (playBtn) {
        playBtn.disabled = !currentSong.audioFile;
        playBtn.textContent = "Play";
    }

    if (feedback) {
        feedback.textContent = currentSong.audioFile
            ? ""
            : "No preview for this track - guess based on the options.";
        feedback.style.color = "";
    }

    if (nextSongBtn) nextSongBtn.style.display = "none";
}

// ===========================================================
// HANDLE GUESS
// ===========================================================
function handleGuess(correct, clickedButton) {
    let listened = accumulatedPlayMs;
    if (playStartTime) {
        listened += performance.now() - playStartTime;
        playStartTime = null;
    }

    audioPlayer.pause();
    if (playBtn) playBtn.textContent = "Play";

    const seconds = Math.max(1, Math.floor(listened / 1000));
    let points = correct ? Math.max(50, 500 - seconds * 25) : 0;

    score += points;
    if (scoreDisplay) scoreDisplay.textContent = `Score: ${score}`;

    const allOptions = document.querySelectorAll(".option-btn");
    allOptions.forEach(btn => {
        btn.disabled = true;
        if (btn.textContent === currentSong.title) {
            btn.classList.add("correct");
        }
    });

    if (!correct && clickedButton) {
        clickedButton.classList.add("wrong");
    }

    if (songTitleEl) songTitleEl.textContent = currentSong.title || "";
    if (songArtistEl) songArtistEl.textContent = currentSong.artist || "";

    if (correct) {
        currentStreak += 1;
        flashFeedback("success");
        playFeedbackTone("success");
    } else {
        currentStreak = 0;
        flashFeedback("error");
        playFeedbackTone("error");
    }

    if (streakDisplay) streakDisplay.textContent = `Streak: ${currentStreak}`;

    if (feedback) {
        if (!correct) {
            feedback.textContent = "Incorrect!";
            feedback.style.color = "#e74c3c";
        } else {
            feedback.textContent = `Correct! (+${points})`;
            feedback.style.color = "#16a34a";
        }
    }

    if (nextSongBtn) nextSongBtn.style.display = "inline-block";
}

// ===========================================================
// END OF ROUND
// ===========================================================
function finalizeRun() {
    finalizeRunHighscore();
    recordScoreToLeaderboard();

    if (feedback) {
        feedback.textContent = `Round complete! Final score: ${score}`;
        feedback.style.color = "#16a34a";
    }

    if (nextSongBtn) nextSongBtn.style.display = "none";
    if (playBtn) playBtn.disabled = true;

    setTimeout(() => resetToMenu(), 2500);
}

// ===========================================================
// RESET TO MENU
// ===========================================================
function resetToMenu() {
    audioPlayer.pause();
    audioPlayer.currentTime = 0;

    if (playBtn) {
        playBtn.disabled = false;
        playBtn.textContent = "Play";
    }

    if (loadingInterval) {
        window.clearInterval(loadingInterval);
        loadingInterval = null;
    }
    if (loadingPanel) {
        loadingPanel.classList.add("is-hidden");
        loadingPanel.style.display = "none";
    }

    currentSong = null;
    currentSongList = [];
    score = 0;
    currentStreak = 0;
    playStartTime = null;
    accumulatedPlayMs = 0;

    if (scoreDisplay) scoreDisplay.textContent = "Score: 0";
    if (streakDisplay) streakDisplay.textContent = "Streak: 0";
    if (feedback) {
        feedback.textContent = "Choose a mode to begin.";
        feedback.style.color = "";
    }

    hideScreen(gameAreaDiv);
    showScreen(genreSelectionDiv);
}

// ===========================================================
// UTILS
// ===========================================================
function shuffleArray(arr) {
    return arr
        .map(a => [Math.random(), a])
        .sort((a, b) => a[0] - b[0])
        .map(a => a[1]);
}

// ===========================================================
// BOOTSTRAP
// ===========================================================
initializeGame();
