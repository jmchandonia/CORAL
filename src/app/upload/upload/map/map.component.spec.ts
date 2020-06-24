import { async, ComponentFixture, TestBed, fakeAsync, tick, flush } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { NgxSpinnerModule } from 'ngx-spinner';
import { HttpClientModule } from '@angular/common/http';
import { MapComponent } from './map.component';
import { ModalModule, BsModalService } from 'ngx-bootstrap/modal';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick } from 'src/app/shared/models/brick';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { of, Subject, Observable, asyncScheduler } from 'rxjs';
import { MockComponent } from 'ng-mocks';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { ValidationErrorItemComponent } from './validation-error-item/validation-error-item.component';

describe('MapComponent', () => {

  const brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);

  const errorSub = new Subject();

  const MockValidator = {
    getValidationErrors: () => errorSub
  }

  const MockModal = {
    show: () => {}
  }

  const MockUploadService = {
    getBrickBuilder: () => brick,
    getValidationResults: () => of({
        results: {
          data_vars: brick.dataValues.map((dataValue, idx) => {
            if (idx % 2 === 0) {
              // every other item is 100% mapped, last item is 0% mapped
              return { valid_count: 100, invalid_count: 0, total_count: 100 }
            } else {
              return { valid_count: 0, invalid_count: 100, total_count: 100 }
            }
          }),
          dims: brick.dimensions.map(dim => {
            return {
              dim_vars: dim.variables.map(variable => {
                if (variable.type.text.includes('Molecule')) {
                  return { valid_count: 50, invalid_count: 50, total_count: 100 }
                } else {
                  return { valid_count: 100, invalid_count: 0, total_count: 100 }
                }
              })
            }
          })
        }
      }, asyncScheduler),
      getDimVarValidationErrors: () => of({results: {}}, asyncScheduler),
      getDataVarValidationErrors: () => of({results: {}}, asyncScheduler)
  };

  let spectator: Spectator<MapComponent>;
  const createComponent = createComponentFactory({
    component: MapComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule,
      ModalModule.forRoot()
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator),
      mockProvider(BsModalService, MockModal)
    ],
    entryComponents: [
      MockComponent(ValidationErrorItemComponent)
    ],
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should render validation results', fakeAsync(() => {
    spyOn(spectator.component, 'getValidationResults').and.callThrough();
    spectator.click('button.get-validation');
    spectator.detectChanges();
    expect(spectator.component.getValidationResults).toHaveBeenCalled();
    tick();
    spectator.detectChanges();

    // check for correct color classes
    expect(spectator.query('table.data-vars-map > tbody > tr:nth-child(1) > td:nth-child(3)'))
      .toHaveClass('stats-column status-column-success');
    expect(spectator.query('table.data-vars-map > tbody > tr:nth-child(2) > td:nth-child(3)'))
      .toHaveClass('stats-column status-column-fail');
    expect(spectator.query('table.dim-vars-map > tbody > tr:last-child > td:nth-child(3)'))
      .toHaveClass('stats-column status-column-warn');

     // check for require mapping tooltip (first item in dim vars list)
    expect(spectator.query('table.dim-vars-map > tbody > tr > td')).toHaveDescendant('i.material-icons');

    // check for links to modal for error items
    expect(spectator.query('table.data-vars-map > tbody > tr > td:nth-child(4)')).toHaveDescendant('span');
    expect(spectator.query('table.data-vars-map > tbody > tr:last-child > td:nth-child(4)')).toHaveDescendant('button');
  }));

  it('should open modal for error items', fakeAsync(() => {
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'getDataVarValidationErrors').and.callThrough();
    spyOn(spectator.component, 'openModal').and.callThrough();
    spectator.detectChanges();
    spectator.component.getValidationResults();
    tick();
    spectator.detectChanges();
    spectator.click('table.data-vars-map > tbody > tr:last-child > td:nth-child(4) > button');
    expect(uploadService.getDataVarValidationErrors).toHaveBeenCalled();
    tick();
    spectator.detectChanges();
    expect(spectator.component.openModal).toHaveBeenCalled();
    flush();
  }));

  it('should render error box', () => {
    errorSub.next(true);
    spectator.detectChanges();
    expect(spectator.component.error).toBeTruthy();
    expect(spectator.query('div.alert.alert-danger')).not.toBeNull();
  });
});
