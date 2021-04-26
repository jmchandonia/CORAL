import { Component, OnInit } from '@angular/core';
import { Router, NavigationEnd, ActivatedRoute } from '@angular/router';
import { AuthService } from './shared/services/auth.service';
import { PlotService } from 'src/app/shared/services/plot.service';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { HomeService } from 'src/app/shared/services/home.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit {
  title = 'coral-ui';
  currentUrl: string;
  homeSearchRedirect = false;
  constructor(
    private router: Router,
    private auth: AuthService,
    private plotService: PlotService,
    private queryBuilder: QueryBuilderService,
    private route: ActivatedRoute,
    private homeService: HomeService
  ) {
    this.router.events.subscribe(event => {
      if (event instanceof NavigationEnd) {
        // remove '?redirect=home' from url to prevent home tab from staying selected
        this.currentUrl = event.url.split('?')[0];
      }
    });

    this.route.queryParams.subscribe(params => {
      if (params['redirect']) {
        this.homeSearchRedirect = true;
      } else {
      }
    });
   }

   async ngOnInit() {
     // send ping to server to makse sure its running
     await this.homeService.initBackendConnection();
   }

   logout() {
     this.auth.logout();
     this.router.navigate(['login']);
   }

   handleHomeNavigation() {
     if (this.homeSearchRedirect) {
       this.queryBuilder.resetObject();
       this.homeSearchRedirect = false;
     }
   }

}
