package com.bustamante.moa_mobile.Utilities;

import android.content.Context;
import android.preference.PreferenceManager;


public class SharedPreference {

    public SharedPreference() {
    }

    public static void setString(String key, String value, Context context) {
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        android.content.SharedPreferences.Editor editor = preferences.edit();
        editor.putString(key, value);
        editor.commit();
    }

    public static void setBoolean(String key, Boolean value, Context context){
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        android.content.SharedPreferences.Editor editor = preferences.edit();
        editor.putBoolean(key, value);
        editor.commit();
    }

    public static void setInt(String key, int value, Context context){
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        android.content.SharedPreferences.Editor editor = preferences.edit();
        editor.putInt(key, value);
        editor.commit();
    }

    public static String getString(String key, Context context) {
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        return preferences.getString(key, null);
    }

    public static boolean getBool(String key, Context context){
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        return preferences.getBoolean(key, false);
    }

    public static boolean getFirstLogin(String key, Context context){
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        return preferences.getBoolean(key, true);
    }

    public static int getInt(String key, Context context){
        android.content.SharedPreferences preferences = PreferenceManager.getDefaultSharedPreferences(context);
        return preferences.getInt(key, 0);
    }
}