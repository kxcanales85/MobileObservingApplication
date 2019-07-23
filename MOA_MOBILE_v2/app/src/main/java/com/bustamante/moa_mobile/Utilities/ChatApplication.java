package com.bustamante.moa_mobile.Utilities;

import android.app.Application;

import java.net.URISyntaxException;

import io.socket.client.IO;
import io.socket.client.Socket;
import static com.bustamante.moa_mobile.R.string.port_socket;
import static com.bustamante.moa_mobile.R.string.url_host;

public class ChatApplication extends Application {

    private Socket mSocket;
    {
        try {
            mSocket = IO.socket(url_host+":"+port_socket);
        } catch (URISyntaxException e) {
            throw new RuntimeException(e);
        }
    }

    public Socket getSocket() {
        return mSocket;
    }
}
