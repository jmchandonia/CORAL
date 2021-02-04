import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { UploadComponent } from './upload.component';
import { RouterModule } from '@angular/router';
import { HttpClientModule } from '@angular/common/http';
import { Router, NavigationEnd } from '@angular/router';
import { of } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { UploadService } from 'src/app/shared/services/upload.service';

describe('UploadComponent', () => {

  let spectator: Spectator<UploadComponent>;
  const createComponent = createComponentFactory({
    component: UploadComponent,
    imports: [
      RouterModule.forRoot([]),
      HttpClientModule
    ],
    providers: [
      {
        provide: Router,
        useValue: {
          events: of(new NavigationEnd(0, '/upload/data-variables', '/upload/data-variables')),
          navigate: url => {}
        }
      },
      {
        provide: UploadValidationService,
        useValue: {
          validationErrors: url => false
        }
      },
      {
        provide: UploadService,
        useValue: {
          saveBrickBuilder: () => {},
          clearCache: () => {}
        }
      }
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have correct currentURL', () => {
    expect(spectator.component.currentUrl).toBe('data-variables');
    expect(spectator.component.progressIndex).toBe(1);
    expect(spectator.component.maxStep).toBe(1);
  });

  it('should disallow moving forward without completed forms', () => {
    const mockRouter = spectator.fixture.debugElement.injector.get(Router);
    spyOn(spectator.component, 'navigateBreadcrumb');
    spyOn(mockRouter, 'navigate');
    spectator.click('nav ol li.breadcrumb-item:nth-child(3)');
    expect(mockRouter.navigate).not.toHaveBeenCalled();
  });

  it('should have proper nav classes on breadcrumbs', () => {
    expect(spectator.query('nav ol li.breadcrumb-item:nth-child(2)')).toHaveClass('active');
    expect(spectator.query('nav ol li.breadcrumb-item:nth-child(3)')).toHaveClass('incomplete');
    expect(spectator.query('nav ol li.breadcrumb-item:nth-child(1)')).toHaveClass('complete');
  });

  it('should navigate forwards', () => {
    const mockRouter = spectator.fixture.debugElement.injector.get(Router);
    const mockValidator = spectator.fixture.debugElement.injector.get(UploadValidationService);
    const uploadService = spectator.debugElement.injector.get(UploadService);
    
    spyOn(mockValidator, 'validationErrors');
    spyOn(uploadService, 'saveBrickBuilder');
    spyOn(mockRouter, 'navigate');
    spectator.click('button.next-step');
    
    expect(mockValidator.validationErrors).toHaveBeenCalled();
    expect(uploadService.saveBrickBuilder).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/upload/dimensions']);
    expect(spectator.component.progressIndex).toEqual(2);
  });

  it('should navigate backwards', () => {
    const mockRouter = spectator.fixture.debugElement.injector.get(Router);
    const uploadService = spectator.debugElement.injector.get(UploadService);
    
    spyOn(uploadService, 'saveBrickBuilder');
    spyOn(mockRouter, 'navigate');
    spectator.click('button.previous-step');
    
    expect(spectator.component.progressIndex).toEqual(0);
    expect(uploadService.saveBrickBuilder).toHaveBeenCalled();
    expect(mockRouter.navigate).toHaveBeenCalledWith(['/upload/type']);
  });

  it('should clear cache on destroy', () => {
    const uploadService = spectator.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'clearCache');

    spectator.component.ngOnDestroy();
    expect(uploadService.clearCache).toHaveBeenCalled();
  });
});
