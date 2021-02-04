import { BrowserModule } from '@angular/platform-browser';
import { NgModule, ErrorHandler } from '@angular/core';
import { SearchModule } from './search/search.module';
import { AppRoutingModule } from './app-routing.module';
import { AppComponent } from './app.component';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { PlotModule } from './plot/plot.module';
import { PlotlyViaWindowModule } from 'angular-plotly.js';
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
import { NgSelectModule } from '@ng-select/ng-select';
import { TreeModule } from 'angular-tree-component';
import { ProvenanceGraphComponent } from './shared/components/provenance-graph/provenance-graph.component';
import { ResizableModule } from 'angular-resizable-element'
import { AuthInterceptor } from 'src/app/shared/services/auth-interceptor';
import { AgmCoreModule } from '@agm/core';
import { environment }  from 'src/environments/environment';
import { NgxSliderModule } from '@angular-slider/ngx-slider';
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
    ProvenanceGraphComponent,
  ],
  imports: [
    BrowserModule,
    AppRoutingModule,
    SearchModule,
    HttpClientModule,
    PlotModule,
    NgxSpinnerModule,
    FormsModule,
    UploadModule,
    ModalModule.forRoot(),
    TooltipModule.forRoot(),
    NgSelectModule,
    TreeModule.forRoot(),
    ResizableModule,
    PlotlyViaWindowModule,
    AgmCoreModule.forRoot({
      apiKey: environment.GOOGLE_MAPS_API_KEY
    }),
    NgxSliderModule
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
    },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: AuthInterceptor,
      multi: true
    }
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
