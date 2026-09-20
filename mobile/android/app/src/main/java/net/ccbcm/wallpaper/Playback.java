package net.ccbcm.wallpaper;
import android.content.Context;
import android.net.Uri;
import android.view.SurfaceHolder;
import androidx.media3.common.*;
import androidx.media3.exoplayer.*;
import java.io.File;
final class Playback {
 static ExoPlayer open(Context context,File file,SurfaceHolder surface,Player.Listener listener){
  DefaultRenderersFactory renderers=new DefaultRenderersFactory(context).setEnableDecoderFallback(true);
  ExoPlayer player=new ExoPlayer.Builder(context,renderers).build();
  player.setTrackSelectionParameters(player.getTrackSelectionParameters().buildUpon().setTrackTypeDisabled(C.TRACK_TYPE_AUDIO,true).build());
  player.setVolume(0);player.setRepeatMode(Player.REPEAT_MODE_ONE);
  player.setVideoScalingMode(C.VIDEO_SCALING_MODE_SCALE_TO_FIT_WITH_CROPPING);
  player.addListener(listener);player.setVideoSurfaceHolder(surface);
  player.setMediaItem(MediaItem.fromUri(Uri.fromFile(file)));player.prepare();return player;
 }
}
