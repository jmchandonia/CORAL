import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { AuthService } from './shared/services/auth.service';
import { PlotService } from 'src/app/shared/services/plot.service';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'generix-ui';
  currentUrl: string;
  homeSearchRedirect = false;
  constructor(
    private router: Router,
    private auth: AuthService,
    private plotService: PlotService,
    private queryBuilder: QueryBuilderService,
    private route: ActivatedRoute
  ) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        this.currentUrl = event.url;
      }
    });

    this.route.queryParams.subscribe(params => {
      if (params['redirect']) {
        this.homeSearchRedirect = true;
      } else {
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
     if (this.homeSearchRedirect) {
       this.queryBuilder.resetObject();
       this.homeSearchRedirect = false;
     }
   }

}
