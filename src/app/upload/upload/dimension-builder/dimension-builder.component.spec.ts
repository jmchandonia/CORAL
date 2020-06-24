import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { MockComponent } from 'ng-mocks';
import { DimensionFormComponent } from './dimension-form/dimension-form.component';
import { DimensionBuilderComponent } from './dimension-builder.component';
import { HttpClientModule } from '@angular/common/http';
import { Brick } from 'src/app/shared/models/brick';
import { UploadService } from 'src/app/shared/services/upload.service';
const metadata = require('src/app/shared/test/brick-type-templates.json');
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { Subject } from 'rxjs';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';

describe('DimensionBuilderComponent', () => {

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);
  const errorSub = new Subject();

  const MockUploadService = {
    getBrickBuilder: () => brick,
    validateDimensions: () => {}
  }

  const MockValidator = {
    getValidationErrors: () => errorSub
  }

  let spectator: Spectator<DimensionBuilderComponent>;
  const createComponent = createComponentFactory({
    component: DimensionBuilderComponent,
    entryComponents: [
      MockComponent(DimensionFormComponent)
    ],
    imports: [
      HttpClientModule,
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator)
    ]
  });

  beforeEach(() => spectator = createComponent());


  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });

  it('should have brick upload instance', () => {
    expect(spectator.component.brick instanceof Brick).toBeTruthy();
    expect(spectator.component.brick.template_type).toBe('Test Chemical Measurement');
    expect(spectator.component.brick.dimensions).toHaveLength(2);
  });

  it('should add dimensions on click', () => {
    spyOn(spectator.component, 'addDimension').and.callThrough();
    spectator.click('button.add-dimension');
    expect(spectator.component.addDimension).toHaveBeenCalled();
    expect(spectator.component.brick.dimensions.length).toBe(3);
    expect(spectator.queryAll('app-dimension-form')).toHaveLength(3);
  });

  it('should remove dimensions', () => {
    spyOn(spectator.component, 'validate');
    spyOn(spectator.component, 'removeDimension').and.callThrough();
    spyOn(spectator.component.brick, 'resetDimensionIndices');
    spectator.triggerEventHandler('app-dimension-form', 'deleted', spectator.component.brick.dimensions[2]);
    spectator.detectChanges();
    expect(spectator.component.removeDimension).toHaveBeenCalled();
    expect(spectator.component.brick.dimensions).toHaveLength(2);
    expect(spectator.component.brick.resetDimensionIndices).toHaveBeenCalled();
    expect(spectator.component.validate).toHaveBeenCalled();
  });

  it('should receive and display errors from validator', async(() => {
    const validator = spectator.fixture.debugElement.injector.get(UploadValidationService);
    spectator.fixture.whenStable().then(() => {
      errorSub.next(true);
      spectator.detectChanges();
      expect(spectator.component.error).toBeTruthy();
      expect(spectator.query('div.alert.alert-danger')).toBeTruthy();

      // call validation 
      spectator.component.validate();
      expect(validator.validateDimensions).toHaveBeenCalled();
    });
  }));
});
