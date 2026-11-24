package io.github.pctecnikk.enlacespanel;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.os.Handler;
import android.os.Looper;
import android.text.InputType;
import android.view.Gravity;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.inputmethod.EditorInfo;
import android.webkit.CookieManager;
import android.webkit.JavascriptInterface;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.EditText;
import android.widget.FrameLayout;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * App de EnlacesPanel: el panel de tu propio servidor dentro de una app.
 * Se guardan dos direcciones: la principal (normalmente tu dominio con https) y,
 * si quieres, la de casa (IP de la wifi). Si una no responde, se prueba la otra sola.
 */
public class MainActivity extends Activity {

    private static final String PREFS = "enlacespanel";
    private static final String KEY_URL = "server_url";
    private static final String KEY_ALT = "server_alt";
    private static final String ACTION_CHANGE_SERVER = "io.github.pctecnikk.enlacespanel.CHANGE_SERVER";
    private static final String ACTION_NOVEDADES = "io.github.pctecnikk.enlacespanel.NOVEDADES";
    private static final String INSTALL_URL = "https://github.com/pctecnikk/enlacespanel#2-instalar";
    private static final int REQ_FILES = 1;
    private static final int REQ_STORAGE = 2;
    private static final int RED = 0xFFE4002B;
    private static final int INK = 0xFF111111;
    private static final int GREY = 0xFF6B6B6B;

    private SharedPreferences prefs;
    private FrameLayout root;
    private WebView web;
    private ProgressBar progress;
    private ValueCallback<Uri[]> fileCallback;
    private String base;            // direccion que se esta usando ahora
    private boolean triedOther;     // ya se probo la otra direccion tras un fallo
    private boolean errorShown;
    private String[] pendingDownload;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);
        root = new FrameLayout(this);
        root.setBackgroundColor(Color.WHITE);
        setContentView(root);

        String url = prefs.getString(KEY_URL, null);
        if (url == null || isAction(getIntent(), ACTION_CHANGE_SERVER)) {
            showSetup(null);
        } else {
            showWeb(url, state);
        }
        if (state == null) Novedades.showIfUpdated(this, prefs, url == null);
        if (isAction(getIntent(), ACTION_NOVEDADES)) Novedades.show(this, prefs, null);
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        if (isAction(intent, ACTION_CHANGE_SERVER)) showSetup(null);
        else if (isAction(intent, ACTION_NOVEDADES)) Novedades.show(this, prefs, null);
    }

    private static boolean isAction(Intent i, String action) {
        return i != null && action.equals(i.getAction());
    }

    // ------------------------------------------------------------------ Pantalla de conexion

    private void showSetup(String message) {
        if (web != null) {
            web.destroy();
            web = null;
        }
        root.removeAllViews();

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout box = new LinearLayout(this);
        box.setOrientation(LinearLayout.VERTICAL);
        box.setGravity(Gravity.CENTER_HORIZONTAL);
        box.setPadding(dp(28), dp(44), dp(28), dp(28));
        scroll.addView(box);

        android.widget.ImageView logo = new android.widget.ImageView(this);
        logo.setImageResource(R.mipmap.ic_launcher);
        box.addView(logo, new LinearLayout.LayoutParams(dp(84), dp(84)));

        TextView title = new TextView(this);
        title.setText("EnlacesPanel");
        title.setTextSize(30);
        title.setTypeface(Typeface.DEFAULT_BOLD);
        title.setTextColor(INK);
        title.setGravity(Gravity.CENTER);
        title.setPadding(0, dp(10), 0, dp(4));
        box.addView(title);

        TextView info = text("Conecta la app con tu servidor EnlacesPanel. Escribe la misma dirección que usas en el navegador.", 15, 0xFF333333);
        info.setPadding(0, dp(4), 0, dp(16));
        box.addView(info);

        TextView need = text("Importante: necesitas tu propio servidor EnlacesPanel ya instalado "
                + "(en una Raspberry Pi o un ordenador con Linux y Docker). Sin servidor la app no funciona.\n"
                + "¿Aún no lo tienes? Toca aquí para ver cómo instalarlo.", 14, 0xFF7A1F00);
        need.setPadding(dp(14), dp(12), dp(14), dp(12));
        GradientDrawable nbg = new GradientDrawable();
        nbg.setColor(0xFFFFF1F2);
        nbg.setCornerRadius(dp(10));
        need.setBackground(nbg);
        need.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) {
            Novedades.open(MainActivity.this, INSTALL_URL);
        } });
        LinearLayout.LayoutParams nlp = matchWrap();
        nlp.setMargins(0, 0, 0, dp(18));
        box.addView(need, nlp);

        box.addView(label("Dirección de tu servidor"));
        box.addView(text("Lo normal es tu dominio, que funciona desde cualquier sitio: "
                + "por ejemplo enlaces.midominio.com", 13, GREY));
        final EditText main = input("enlaces.midominio.com", prefs.getString(KEY_URL, ""));
        box.addView(main, matchWrap());

        box.addView(label("Dirección en casa (opcional)"));
        box.addView(text("La IP de tu servidor en la wifi de casa y el puerto, por ejemplo 192.168.1.50:8092. "
                + "Si pones las dos, la app usa sola la que funcione.", 13, GREY));
        final EditText alt = input("192.168.1.50:8092", prefs.getString(KEY_ALT, ""));
        alt.setImeOptions(EditorInfo.IME_ACTION_GO);
        box.addView(alt, matchWrap());

        final TextView status = text(message != null ? message : "", 14, RED);
        status.setGravity(Gravity.CENTER);
        status.setPadding(0, dp(12), 0, dp(12));
        box.addView(status);

        final Button connect = new Button(this);
        connect.setText("Conectar");
        connect.setTextColor(Color.WHITE);
        connect.setAllCaps(false);
        connect.setTextSize(16);
        GradientDrawable cbg = new GradientDrawable();
        cbg.setColor(INK);
        cbg.setCornerRadius(dp(10));
        connect.setBackground(cbg);
        box.addView(connect, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52)));

        final Runnable go = new Runnable() { @Override public void run() {
            final String u1 = normalize(main.getText().toString());
            final String u2 = alt.getText().toString().trim().isEmpty() ? "" : normalize(alt.getText().toString());
            if (u1 == null && (u2 == null || u2.isEmpty())) {
                status.setText("Escribe al menos una dirección válida.");
                return;
            }
            if (u2 == null) {
                status.setText("La dirección de casa no parece válida.");
                return;
            }
            final String first = u1 != null ? u1 : u2;
            final String second = u1 != null ? u2 : "";
            connect.setEnabled(false);
            status.setTextColor(GREY);
            status.setText("Comprobando " + first + " …");
            checkServer(first, new CheckResult() { @Override public void done(boolean ok, String error) {
                if (ok) { connect.setEnabled(true); saveAndOpen(first, second); return; }
                if (!second.isEmpty()) {
                    status.setText("Comprobando " + second + " …");
                    checkServer(second, new CheckResult() { @Override public void done(boolean ok2, String error2) {
                        connect.setEnabled(true);
                        if (ok2) {
                            toast("Ahora entras por la dirección de casa. Fuera de casa se usará " + first);
                            saveAndOpen(second, first);
                            return;
                        }
                        fail(status, first, second, error);
                    } });
                    return;
                }
                connect.setEnabled(true);
                fail(status, first, second, error);
            } });
        } };
        connect.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { go.run(); } });
        alt.setOnEditorActionListener(new TextView.OnEditorActionListener() { @Override public boolean onEditorAction(TextView v, int actionId, KeyEvent event) {
            if (actionId == EditorInfo.IME_ACTION_GO
                    || (event != null && event.getKeyCode() == KeyEvent.KEYCODE_ENTER && event.getAction() == KeyEvent.ACTION_DOWN)) {
                go.run();
                return true;
            }
            return false;
        } });

        TextView help = text("\nSi tu dominio no usa https, escribe la dirección completa con http://\n"
                + "Puedes cambiar las direcciones cuando quieras: mantén pulsado el icono de EnlacesPanel "
                + "y elige «Cambiar servidor», o pulsa Atrás dentro de la app.", 13, GREY);
        help.setGravity(Gravity.CENTER);
        box.addView(help);

        TextView ver = text("\nVersión " + Novedades.version(this) + " · Ver novedades", 13, RED);
        ver.setGravity(Gravity.CENTER);
        ver.setPadding(0, dp(8), 0, dp(8));
        ver.setOnClickListener(new View.OnClickListener() { @Override public void onClick(View v) { Novedades.show(MainActivity.this, prefs, null); } });
        box.addView(ver);

        root.addView(scroll);
    }

    private void fail(TextView status, final String first, final String second, String error) {
        status.setTextColor(RED);
        status.setText(error);
        new AlertDialog.Builder(this)
                .setTitle("No se ha podido comprobar")
                .setMessage(error + "\n\n¿Quieres guardar estas direcciones de todas formas?")
                .setPositiveButton("Guardar", new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) { saveAndOpen(first, second); } })
                .setNegativeButton("Corregir", null)
                .show();
    }

    private TextView text(String s, int sp, int color) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        return t;
    }

    private TextView label(String s) {
        TextView t = text(s, 15, INK);
        t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding(0, dp(10), 0, dp(2));
        t.setLayoutParams(matchWrap());
        return t;
    }

    private EditText input(String hint, String value) {
        EditText e = new EditText(this);
        e.setHint(hint);
        e.setSingleLine(true);
        e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_URI);
        e.setImeOptions(EditorInfo.IME_ACTION_NEXT);
        e.setText(value);
        return e;
    }

    private static LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
    }

    /**
     * Convierte lo que escribe la persona en una direccion completa, o null si no vale.
     * Sin http(s):// delante: una IP de casa o un nombre .local van con http://;
     * un dominio va con https://, que es lo normal en Internet.
     */
    static String normalize(String s) {
        if (s == null) return null;
        s = s.trim();
        if (s.isEmpty() || s.contains(" ")) return null;
        if (!s.matches("(?i)^https?://.*")) {
            String host = s.split("[:/]")[0].toLowerCase();
            boolean local = host.matches("^\\d{1,3}(\\.\\d{1,3}){3}$") || host.equals("localhost")
                    || host.endsWith(".local") || host.endsWith(".lan") || !host.contains(".");
            s = (local ? "http://" : "https://") + s;
        }
        while (s.endsWith("/")) s = s.substring(0, s.length() - 1);
        if (s.toLowerCase().endsWith("/panel")) s = s.substring(0, s.length() - 6);
        Uri u = Uri.parse(s);
        if (u.getHost() == null || u.getHost().isEmpty()) return null;
        return s;
    }

    private interface CheckResult { void done(boolean ok, String error); }

    /** Pide el manifest de la web para comprobar que al otro lado hay un EnlacesPanel. */
    private void checkServer(final String url, final CheckResult cb) {
        final Handler main = new Handler(Looper.getMainLooper());
        new Thread(new Runnable() { @Override public void run() {
            boolean ok = false;
            String error;
            HttpURLConnection c = null;
            try {
                c = (HttpURLConnection) new URL(url + "/static/manifest.webmanifest").openConnection();
                c.setConnectTimeout(7000);
                c.setReadTimeout(7000);
                int code = c.getResponseCode();
                if (code == 200) {
                    InputStream in = c.getInputStream();
                    byte[] buf = new byte[4096];
                    int n = in.read(buf);
                    String body = n > 0 ? new String(buf, 0, n, "UTF-8") : "";
                    in.close();
                    ok = body.contains("EnlacesPanel");
                    error = ok ? null : "Esa dirección responde, pero no parece un servidor EnlacesPanel.";
                } else {
                    error = "El servidor ha respondido con un error (" + code + ").";
                }
            } catch (javax.net.ssl.SSLException e) {
                error = "Problema con el certificado https del servidor. Si tu servidor no usa https, escribe la dirección con http://";
            } catch (java.net.UnknownHostException e) {
                error = "No se encuentra esa dirección. Revisa que esté bien escrita.";
            } catch (java.net.SocketTimeoutException e) {
                error = "El servidor no contesta. Si has puesto la IP de casa, comprueba que estás conectado a la wifi de casa.";
            } catch (Exception e) {
                error = "No se puede conectar. Si has puesto la IP de casa, comprueba que estás conectado a la wifi de casa.";
            } finally {
                if (c != null) c.disconnect();
            }
            final boolean fOk = ok;
            final String fErr = error;
            main.post(new Runnable() { @Override public void run() { cb.done(fOk, fErr); } });
        } }).start();
    }

    private void saveAndOpen(String url, String alt) {
        prefs.edit().putString(KEY_URL, url).putString(KEY_ALT, alt == null ? "" : alt).apply();
        showWeb(url, null);
    }

    // ------------------------------------------------------------------ La web

    private void showWeb(final String url, Bundle state) {
        root.removeAllViews();
        base = url;
        errorShown = false;
        web = new WebView(this);
        progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progress.setMax(100);
        root.addView(web, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        root.addView(progress, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(3)));

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setAllowFileAccess(false);
        s.setSupportMultipleWindows(false); // "Ver mi página" se abre dentro de la app
        s.setUserAgentString(s.getUserAgentString() + " EnlacesPanelAndroid/" + Novedades.version(this));

        CookieManager cm = CookieManager.getInstance();
        cm.setAcceptCookie(true);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
                Uri u = req.getUrl();
                String scheme = u.getScheme();
                if (("http".equals(scheme) || "https".equals(scheme)) && isOurHost(u)) {
                    // /go/123 lleva a otra web: se abre fuera para que la app sea solo tu panel
                    if (u.getPath() != null && u.getPath().startsWith("/go/")) { openOutside(u); return true; }
                    return false;
                }
                openOutside(u);
                return true;
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest req, WebResourceError err) {
                if (req.isForMainFrame()) connectionFailed();
            }

            @Override
            public void onPageFinished(WebView view, String u) {
                CookieManager.getInstance().flush();
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int p) {
                progress.setProgress(p);
                progress.setVisibility(p >= 100 ? View.GONE : View.VISIBLE);
            }

            @Override
            public boolean onShowFileChooser(WebView view, ValueCallback<Uri[]> cb, FileChooserParams params) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = cb;
                Intent i = new Intent(Intent.ACTION_GET_CONTENT);
                i.addCategory(Intent.CATEGORY_OPENABLE);
                i.setType("image/*");
                try {
                    startActivityForResult(Intent.createChooser(i, "Elegir foto"), REQ_FILES);
                } catch (ActivityNotFoundException e) {
                    fileCallback = null;
                    toast("No hay ninguna app para elegir fotos");
                    return false;
                }
                return true;
            }
        });

        web.addJavascriptInterface(new Bridge(this), "EnlacesPanelAndroid");

        web.setDownloadListener(new android.webkit.DownloadListener() { @Override public void onDownloadStart(String u, String userAgent, String disposition, String mime, long length) {
            download(new String[]{u, userAgent, disposition, mime});
        } });

        Novedades.check(this, prefs, false);
        if (state != null && web.restoreState(state) != null) return;
        web.loadUrl(base + "/panel");
    }

    private boolean isOurHost(Uri u) {
        String h = u.getHost();
        if (h == null) return false;
        for (String b : new String[]{prefs.getString(KEY_URL, ""), prefs.getString(KEY_ALT, "")}) {
            if (b != null && !b.isEmpty() && h.equalsIgnoreCase(Uri.parse(b).getHost())) return true;
        }
        return false;
    }

    private void openOutside(Uri u) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, u));
        } catch (ActivityNotFoundException e) {
            toast("No hay ninguna app para abrir este enlace");
        }
    }

    /** La direccion actual no responde: se prueba la otra (casa o dominio) antes de avisar. */
    private void connectionFailed() {
        String alt = prefs.getString(KEY_ALT, "");
        if (!triedOther && alt != null && !alt.isEmpty() && !alt.equals(base)) {
            triedOther = true;
            final String other = alt;
            checkServer(other, new CheckResult() { @Override public void done(boolean ok, String error) {
                if (ok) {
                    String cur = base;
                    prefs.edit().putString(KEY_URL, other).putString(KEY_ALT, cur).apply();
                    toast("Conectado por " + other);
                    showWeb(other, null);
                } else {
                    showConnectionError();
                }
            } });
            return;
        }
        showConnectionError();
    }

    private void showConnectionError() {
        if (errorShown || isFinishing()) return;
        errorShown = true;
        new AlertDialog.Builder(this)
                .setTitle("No se puede conectar")
                .setMessage("Tu servidor EnlacesPanel no responde (" + base + ").\n\n"
                        + "Si usas la IP de casa, comprueba que estás en la wifi de casa. "
                        + "Fuera de casa necesitas la dirección con tu dominio.")
                .setPositiveButton("Reintentar", new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) {
                    errorShown = false;
                    triedOther = false;
                    if (web != null) web.loadUrl(base + "/panel");
                } })
                .setNegativeButton("Cambiar servidor", new DialogInterface.OnClickListener() { @Override public void onClick(DialogInterface d, int w) { showSetup(null); } })
                .setCancelable(false)
                .show();
    }

    // ------------------------------------------------------------------ Descargas (QR, tus datos)

    private void download(String[] d) {
        if (Build.VERSION.SDK_INT <= 28 && checkSelfPermission(Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED) {
            pendingDownload = d;
            requestPermissions(new String[]{Manifest.permission.WRITE_EXTERNAL_STORAGE}, REQ_STORAGE);
            return;
        }
        try {
            String name = URLUtil.guessFileName(d[0], d[2], d[3]);
            DownloadManager.Request r = new DownloadManager.Request(Uri.parse(d[0]));
            String cookie = CookieManager.getInstance().getCookie(d[0]);
            if (cookie != null) r.addRequestHeader("Cookie", cookie);
            r.addRequestHeader("User-Agent", d[1]);
            r.setTitle(name);
            r.setMimeType(d[3]);
            r.setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
            r.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
            ((DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE)).enqueue(r);
            toast("Descargando " + name + " en la carpeta Descargas");
        } catch (Exception e) {
            toast("No se ha podido descargar");
        }
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        if (code == REQ_STORAGE && pendingDownload != null) {
            String[] d = pendingDownload;
            pendingDownload = null;
            if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) download(d);
            else toast("Sin permiso no se puede guardar la descarga");
        }
    }

    @Override
    protected void onActivityResult(int req, int result, Intent data) {
        if (req == REQ_FILES && fileCallback != null) {
            Uri[] res = null;
            if (result == RESULT_OK && data != null && data.getData() != null) res = new Uri[]{data.getData()};
            fileCallback.onReceiveValue(res);
            fileCallback = null;
            return;
        }
        super.onActivityResult(req, result, data);
    }

    // ------------------------------------------------------------------ Puente con la web

    /** La web lo usa para compartir y copiar el enlace de tu página (ver app.js). */
    public static final class Bridge {
        private final MainActivity a;
        Bridge(MainActivity a) { this.a = a; }

        @JavascriptInterface
        public void share(final String url, final String title) {
            a.runOnUiThread(new Runnable() { @Override public void run() {
                Intent i = new Intent(Intent.ACTION_SEND);
                i.setType("text/plain");
                i.putExtra(Intent.EXTRA_TEXT, url);
                if (title != null) i.putExtra(Intent.EXTRA_SUBJECT, title);
                a.startActivity(Intent.createChooser(i, "Compartir tu página"));
            } });
        }

        @JavascriptInterface
        public void copy(final String text) {
            a.runOnUiThread(new Runnable() { @Override public void run() {
                ClipboardManager cm = (ClipboardManager) a.getSystemService(Context.CLIPBOARD_SERVICE);
                cm.setPrimaryClip(ClipData.newPlainText("EnlacesPanel", text));
                a.toast("Enlace copiado");
            } });
        }

        @JavascriptInterface
        public String version() { return Novedades.version(a); }
    }

    // ------------------------------------------------------------------ Atrás y ciclo de vida

    @Override
    public void onBackPressed() {
        if (web != null && web.canGoBack()) {
            web.goBack();
            return;
        }
        if (web == null) {
            if (prefs.getString(KEY_URL, null) != null) showWeb(prefs.getString(KEY_URL, null), null);
            else super.onBackPressed();
            return;
        }
        new AlertDialog.Builder(this)
                .setTitle("EnlacesPanel")
                .setItems(new CharSequence[]{"Salir", "Cambiar servidor", "Recargar",
                        "Novedades (versión " + Novedades.version(this) + ")"}, new DialogInterface.OnClickListener() {
                    @Override public void onClick(DialogInterface d, int which) {
                        if (which == 0) finish();
                        else if (which == 1) showSetup(null);
                        else if (which == 2) { triedOther = false; errorShown = false; web.reload(); }
                        else Novedades.show(MainActivity.this, prefs, null);
                    }
                })
                .show();
    }

    @Override
    protected void onSaveInstanceState(Bundle out) {
        super.onSaveInstanceState(out);
        if (web != null) web.saveState(out);
    }

    @Override
    protected void onPause() {
        super.onPause();
        CookieManager.getInstance().flush();
        if (web != null) web.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (web != null) web.destroy();
        super.onDestroy();
    }

    void toast(String msg) {
        Toast.makeText(this, msg, Toast.LENGTH_LONG).show();
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }
}
