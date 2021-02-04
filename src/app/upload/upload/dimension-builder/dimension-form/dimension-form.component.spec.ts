import { async, ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { DimensionFormComponent } from './dimension-form.component';
import { DimensionVariableFormComponent } from './dimension-variable-form/dimension-variable-form.component';
import { BrickDimension, Brick, MicroType } from 'src/app/shared/models/brick';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { By } from '@angular/platform-browser';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
import { Subject, of, asyncScheduler, Observable } from 'rxjs';
import { UploadService } from 'src/app/shared/services/upload.service';
import { NgSelectModule } from '@ng-select/ng-select';
import { FormsModule } from '@angular/forms';

describe('DimensionFormComponent', () => {

  const errorSub = new Subject();

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);
  const dimensions = brick.dimensions;
  let dimension: BrickDimension = dimensions[0];

  const MockUploadService = {
    searchDimensionMicroTypes: (microtype: MicroType): Observable<any> => of({
      results: [{id: '123', text: 'test', has_units: false}]
    }, asyncScheduler)
  };

  let spectator: Spectator<DimensionFormComponent>;
  const createComponent = createComponentFactory({
    component: DimensionFormComponent,
    imports: [
      HttpClientModule,
      NgSelectModule,
      FormsModule
    ],
    entryComponents: [
      MockComponent(DimensionVariableFormComponent)
    ],
    providers: [
      {
        provide: UploadValidationService,
        useValue: {
          validateDimensions: () => {},
          getValidationErrors: () => errorSub
        }
      },
      mockProvider(UploadService, MockUploadService)
    ]
  });

  beforeEach(() => spectator = createComponent({
    props: {
      dimension: dimension
    }
  }));

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have instance of brick dimension', () => {
    expect(spectator.component.dimension instanceof BrickDimension).toBeTruthy();
    expect(spectator.component.dimension.type.text).toBe('Environmental Sample');
    expect(spectator.component.dimension.variables).toHaveLength(4);
  });

  it('should disallow editing required dimensions', () => {
    const selectEl = spectator.debugElement.query(By.css('ng-select'));
    expect(spectator.component.selectedType).toBe('ME:XXXXXX3');
    expect(selectEl.nativeElement.getAttribute('ng-reflect-readonly')).toBe('true');
    expect(spectator.query('button#delete-dimension')).toBeNull();
  });

  it('should add dimension variables', () => {
    spyOn(spectator.component, 'addDimensionVariable').and.callThrough();
    spectator.click('button#add-dimension-variable');
    expect(spectator.component.dimension.variables).toHaveLength(5);
  });

  it('should delete dimension variables', () => {
    spyOn(spectator.component, 'validate');
    spyOn(spectator.component.dimension, 'resetDimVarIndices');
    spyOn(spectator.component, 'removeDimensionVariable').and.callThrough();
    spectator.triggerEventHandler(
      'app-dimension-variable-form',
      'deleted',
      spectator.component.dimension.variables[4]
      );
    expect(spectator.component.removeDimensionVariable).toHaveBeenCalled();
    expect(spectator.component.dimension.variables).toHaveLength(4);
    expect(spectator.component.validate).toHaveBeenCalled();
    expect(spectator.component.dimension.resetDimVarIndices).toHaveBeenCalled();

    // reset dimension to editable dimension for edit tests
    dimension = new BrickDimension(brick, 2, false);
  });

  it('should call search query for dimension types', fakeAsync(() => {
    spectator.detectChanges();
    const uploadService = spectator.fixture.debugElement.injector.get(UploadService);
    spyOn(uploadService, 'searchDimensionMicroTypes').and.callThrough();
    spectator.fixture.whenStable().then(() => {
      spectator.click('span');
      spectator.detectChanges();
      spectator.typeInElement('test', 'input');
      tick();
      spectator.detectChanges();
      expect(uploadService.searchDimensionMicroTypes).toHaveBeenCalledWith('test');
      expect(spectator.component.data).toEqual([{id: '123', text: 'test', has_units: false}]);
    });
  }));

  it('should allow type selection for custom dimensions', () => {
    const selectEl = spectator.debugElement.query(By.css('ng-select'));
    expect(selectEl.nativeElement.getAttribute('ng-reflect-readonly')).toBe('false');
  });

  it('should be able to delete custom dimensions', () => {
    spyOn(spectator.component.deleted, 'emit');
    expect(spectator.query('button#delete-dimension')).not.toBeNull();
    spectator.click('button#delete-dimension');
    spectator.detectChanges();
    expect(spectator.component.deleted.emit).toHaveBeenCalled();
  });

  it('should validate dimension with subscription', () => {
    errorSub.next(true);
    spectator.detectChanges();
    expect(spectator.query('ng-select')).toHaveClass('select-error');
  });
});
