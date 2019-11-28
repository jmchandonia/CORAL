import { BrowserModule } from '@angular/platform-browser';
import { NgModule, ErrorHandler } from '@angular/core';
import { SearchModule } from './search/search.module';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { PlotModule } from './plot/plot.module';
import * as PlotlyJS from 'plotly.js/dist/plotly.js';
import { PlotlyModule } from 'angular-plotly.js';
import { LoginComponent } from './shared/components/login/login.component';
import { HomeComponent } from './shared/components/home/home.component';
import { ReportsComponent } from './shared/components/reports/reports.component';
import { DashboardComponent } from './shared/components/dashboard/dashboard.component';
import { NgxSpinnerModule } from 'ngx-spinner';
import { FormsModule } from '@angular/forms';
import { JwtHelperService, JWT_OPTIONS } from '@auth0/angular-jwt';
import { UploadModule } from './upload/upload.module';
import { ModalModule } from 'ngx-bootstrap/modal';
import { TooltipModule } from 'ngx-bootstrap/tooltip';
import { GlobalErrorHandler } from 'src/app/shared/services/global-error-handler';
import { ServerErrorInterceptor } from 'src/app/shared/services/server-error-interceptor';
import { ErrorComponent } from './shared/components/error/error.component';
import { MicrotypeBrowserComponent } from './shared/components/microtype-browser/microtype-browser.component';
import { DashboardPlotComponent } from './shared/components/dashboard/dashboard-plot/dashboard-plot.component';

PlotlyModule.plotlyjs = PlotlyJS;
@NgModule({
  declarations: [
    AppComponent,
    LoginComponent,
    HomeComponent,
    ReportsComponent,
    DashboardComponent,
    ErrorComponent,
    MicrotypeBrowserComponent,
    DashboardPlotComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SearchModule,
    HttpClientModule,
    Select2Module,
    PlotModule,
    NgxSpinnerModule,
    PlotlyModule,
    FormsModule,
    UploadModule,
    ModalModule.forRoot(),
    TooltipModule.forRoot()
  ],
  providers: [
    {
      provide: JWT_OPTIONS,
      useValue: JWT_OPTIONS
    },
    JwtHelperService,
    {
      provide: ErrorHandler,
      useClass: GlobalErrorHandler
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: ServerErrorInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
