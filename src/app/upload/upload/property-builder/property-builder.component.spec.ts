import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory, mockProvider } from '@ngneat/spectator';
import { PropertyBuilderComponent } from './property-builder.component';
import { MockComponent } from 'ng-mocks';
import { HttpClientModule } from '@angular/common/http';
import { PropertyFormComponent } from './property-form/property-form.component';
import { UploadService } from 'src/app/shared/services/upload.service';
import { Brick, TypedProperty } from 'src/app/shared/models/brick';
import { of, Subject } from 'rxjs';
import { BrickFactoryService } from 'src/app/shared/services/brick-factory.service';
import { UploadValidationService } from 'src/app/shared/services/upload-validation.service';
const metadata = require('src/app/shared/test/brick-type-templates.json');

describe('PropertyBuilderComponent', () => {

  const brick: Brick = BrickFactoryService.createUploadInstance(metadata.results[0].children[1]);

  const errorSub = new Subject();

  const MockUploadService = {
    getBrickBuilder: () => brick
  };

  const MockValidator = {
    getValidationErrors: () => errorSub
  }

  let spectator: Spectator<PropertyBuilderComponent>;
  const createComponent = createComponentFactory({
    component: PropertyBuilderComponent,
    entryComponents: [
      MockComponent(PropertyFormComponent)
    ],
    imports: [
      HttpClientModule
    ],
    providers: [
      mockProvider(UploadService, MockUploadService),
      mockProvider(UploadValidationService, MockValidator)
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
    expect(spectator.component.brick instanceof Brick).toBeTruthy();
    expect(spectator.component.properties).toHaveLength(1);
  });

  it('should add properties', () => {
    spyOn(spectator.component, 'addProperty').and.callThrough();
    spectator.click('button.add-property');
    spectator.detectChanges();
    expect(spectator.component.properties).toHaveLength(2);
    expect(spectator.queryAll('app-property-form')).toHaveLength(2);
  });

  it('should remove properties', () => {
    spyOn(spectator.component, 'deleteProperty').and.callThrough();
    spectator.click('button.add-property'); // add a 3rd property to test
    spectator.detectChanges();
    spectator.triggerEventHandler(
      'app-property-form',
      'deleted',
      spectator.component.brick.properties[1]
      );
    spectator.detectChanges();
    expect(spectator.component.deleteProperty).toHaveBeenCalled();
    expect(spectator.component.properties).toHaveLength(2);
    expect(spectator.queryAll('app-property-form')).toHaveLength(2);
  });

  it('should reset properties', () => {
    spyOn(spectator.component, 'resetProperty').and.callThrough();
    spectator.click('button.add-property'); // add a 2nd property to test
    spectator.detectChanges();
    spectator.component.properties[1].scalarType = 'text to be reset';
    spectator.detectChanges();
    spectator.triggerEventHandler(
      'app-property-form',
      'typeReselected',
      spectator.component.properties[1]
    );
    spectator.detectChanges();
    expect(spectator.component.resetProperty).toHaveBeenCalled();
    expect(spectator.component.properties[1].scalarType).toBe('text to be reset');
  });

  it('should handle errors correctly', () => {
    spyOn(spectator.component, 'setValueError').and.callThrough();
    errorSub.next({
      error: true,
      messages: ['message 1', 'message 2']
    });
    spectator.detectChanges();
    expect(spectator.component.errorMessages).toHaveLength(2);
    expect(spectator.component.errors).toBeTruthy();
    expect(spectator.queryAll('div.alert.alert-danger')).toHaveLength(2);
    expect(spectator.query('div.alert.alert-danger')).toHaveText('message 1');
    // set error from property form event
    spectator.triggerEventHandler(
      'app-property-form',
      'valueError',
      'message 3'
    );
    spectator.detectChanges();
    expect(spectator.component.errorMessages).toHaveLength(3);
    expect(spectator.queryAll('div.alert.alert-danger')).toHaveLength(3);
    expect(spectator.component.setValueError).toHaveBeenCalled();
  });
});
