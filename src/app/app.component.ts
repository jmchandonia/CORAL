import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd } from '@angular/router';
import { AuthService } from './shared/services/auth.service';
import { PlotService } from 'src/app/shared/services/plot.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'generix-ui';
  currentUrl: string;
  constructor(
    private router: Router,
    private auth: AuthService,
    private plotService: PlotService
  ) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.currentUrl = event.url;
      }
    });
   }

   ngOnInit() {
   }

   logout() {
     this.auth.logout();
     this.router.navigate(['login']);
   }

   clearPlotBuilder() {
     // method to clear cached plot form before navigating to another tab
     this.plotService.clearPlotBuilder();
   }

}
