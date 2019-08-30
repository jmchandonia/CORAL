import { BrowserModule } from '@angular/platform-browser';
import { NgModule } from '@angular/core';
import { SearchModule } from './search/search.module';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component'; 
import { Select2Module } from 'ng2-select2';

@NgModule({
  declarations: [
    AppComponent
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SearchModule,
    Select2Module,
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
