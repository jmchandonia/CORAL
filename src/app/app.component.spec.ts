import { TestBed, async } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AppComponent } from './app.component';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { JwtHelperService, JWT_OPTIONS } from '@auth0/angular-jwt';
import { QueryBuilderService } from 'src/app/shared/services/query-builder.service';
import { AuthService } from 'src/app/shared/services/auth.service';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Router, ActivatedRoute } from '@angular/router';
import { HttpClientModule } from '@angular/common/http'; 
import { RouterModule } from '@angular/router';
import { of } from 'rxjs';

describe('AppComponent', () => {

  let spectator: Spectator<AppComponent>;

  const createComponent = createComponentFactory({
    component: AppComponent,
    providers: [
      JwtHelperService,
      {
        provide: JWT_OPTIONS,
        useValue: JWT_OPTIONS
      },
      {
        provide: QueryBuilderService,
        useValue: {
          resetObject() {}
        }
      },
      {
        provide: AuthService,
        useValue: {
          logout() {},
          navigate(url) {}
        }
      },
    ],
    imports: [
      HttpClientModule,
      // RouterModule.forRoot([])
      RouterTestingModule,
    ]
  })

  beforeEach(() => spectator = createComponent());

  it('should create the app', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should clear on search click', () => {
    spyOn(spectator.component, 'handleHomeNavigation');
    spectator.component.homeSearchRedirect = true;
    spectator.click('a#search-nav-link');
    spectator.detectChanges();

    expect(spectator.component.handleHomeNavigation).toHaveBeenCalled();
  });

  xit('should sign out', () => {
    const authService = spectator.get(AuthService);
    spyOn(spectator.component, 'logout');
    spyOn(authService, 'logout');
    spectator.click('a#signout-nav-link');
    spectator.detectChanges();

    expect(spectator.component.logout).toHaveBeenCalled();
    expect(authService.logout).toHaveBeenCalled();
  });

});
